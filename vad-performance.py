#!/usr/bin/env python2
import argparse
import sys
import re

def parse_recipe(rfile):
    """Parses input recipe, checks for LNA's"""
    r = []
    rr = []
    audio_file = re.compile('audio=(\S+)')
    start_time = re.compile('start-time=(\d+.\d+)')
    end_time = re.compile('end-time=(\d+.\d+)')
    this_file = ''
    total_entries = 0
    for line in rfile:
        try:
            audio = audio_file.search(line).groups()[0]
            start = float(start_time.search(line).groups()[0])
            end = float(end_time.search(line).groups()[0])
            if audio != this_file:
                if this_file != '':
                    r.append((audio, rr))
                    rr = []
                this_file = audio
            rr.append((start, end))
            total_entries += 1
        except AttributeError:
            print 'Recipe line without recognizable data:'
            print line
    # Append last audio file
    r.append((this_file, rr))
    return r, total_entries

def benchmark(baseline, proposed, threshold, outf):
    """Benchmarks VAD agains baseline ones"""
    noise_as_speech = 0.0
    speech_as_noise = 0.0
    proposed_total_time = 0.0
    proposed_turns = 0
    baseline_total_time = 0.0
    baseline_turns = 0
    for files in xrange(len(baseline)):
        #Both have same audio files, so same number of entries here
        b_iter = iter(baseline[files][1])
        p_iter = iter(proposed[files][1])
        bstart, bend = b_iter.next()
        baseline_turns += 1
        baseline_total_time += bend - bstart
        pstart, pend = p_iter.next()
        proposed_turns += 1
        proposed_total_time += pend - pstart
        while True:
            if pstart + threshold < bstart - threshold:
                if pend + threshold < bstart - threshold:  # Completely out
                    t = pend - pstart
                    noise_as_speech += t
                    if args.ns:
                        print '1.- Noise as speech, from:', pstart, 'to:', \
                            pend, 'missed time:', t, \
                            'total noise as speech:', noise_as_speech
                    try:
                        pstart, pend = p_iter.next()
                    except StopIteration:
                        break
                    proposed_turns += 1
                    proposed_total_time += pend - pstart
                    continue
                else:  # pend + threshold >= bstart - threshold
                    if bstart - pstart > 2.0 * threshold:
                        t = bstart - pstart - 2.0 * threshold
                        noise_as_speech += t
                        if args.ns:
                            print '2.- Noise as speech, from:', pstart, 'to:', \
                                bstart, 'missed time:', t, \
                                'total noise as speech:', noise_as_speech
                    if pend - threshold > bend + threshold:  # Get another baseline
                        pstart = bend
                        try:
                            bstart, bend = b_iter.next()
                        except StopIteration:
                            break
                        baseline_turns += 1
                        baseline_total_time += bend - bstart
                        continue
                    bstart = pend
                    try:
                        pstart, pend = p_iter.next()
                    except StopIteration:
                        break
                    proposed_turns += 1
                    proposed_total_time += pend - pstart
                    continue
            else:  # pstart >= bstart
                if bend + threshold < pstart - threshold:  # Completely out
                    t = bend - bstart
                    speech_as_noise += t
                    if args.sn:
                        print '3.- Speech as Noise, from:', bstart, 'to:', \
                            bend, 'missed time:', t, \
                            'total missed:', speech_as_noise
                    try:
                        bstart, bend = b_iter.next()
                    except StopIteration:
                        break
                    baseline_turns += 1
                    baseline_total_time += bend - bstart
                    continue
                else:
                    if pstart - bstart > 2.0 * threshold:
                        t = pstart - bstart - 2.0 * threshold
                        speech_as_noise += t
                        if args.sn:
                            print '4.- Speech as Noise, from:', bstart, 'to:', \
                                pstart, 'missed time:', t, \
                                'total missed:', speech_as_noise
                    if bend - threshold > pend + threshold:  # Get another proposed
                        bstart = pend
                        try:
                            pstart, pend = p_iter.next()
                        except StopIteration:
                            break
                        proposed_turns += 1
                        proposed_total_time += pend - pstart
                        continue
                    pstart = bend
                    try:
                        bstart, bend = b_iter.next()
                    except StopIteration:
                        break
                    baseline_turns += 1
                    baseline_total_time += bend - bstart
                    continue

        # Is there anything left? Add as error
        first_end = True
        for pstart, pend in p_iter:
            if first_end and (pstart - threshold > bend + threshold):
                t = pend - pstart
                noise_as_speech += t
                if args.ns:
                    print 'Noise as speech, from:', pstart, 'to:', \
                        pend, 'missed time:', t, \
                        'total noise as speech:', noise_as_speech
        first_end = True
        for bstart, bend in b_iter:
            if first_end and (bstart - threshold > pend + threshold):
                first_end = False
                t = bend - bstart
                speech_as_noise += t
                if args.sn:
                    print 'Speech as Noise, from:', bstart, 'to:', \
                        bend, 'missed time:', t, \
                        'total missed:', speech_as_noise


    print_results(speech_as_noise, noise_as_speech,
            baseline_total_time, baseline_turns,
            proposed_total_time, proposed_turns)

def print_results(missed, noise, baseline_total, baseline_turns,
        proposed_total, proposed_turns):
    """Pretty print useful results"""
    print '{0:>48}'.format('Benchmark results:')
    print '{0:>48}'.format('------------------')

    print '{0:<36} {1:^5.3f}'.format('Speech as Noise time:', missed)
    print '{0:<36} {1:^5.3f}'.format('Noise as Speech time:', noise)
    print '{0:<36} {1:^5.3f}'.format('Total baseline speech time:', baseline_total)
    print '{0:<36} {1}'.format('Total baseline turns:', baseline_turns)
    print '{0:<36} {1:^5.3f}'.format('Average baseline turn time:',
            baseline_total/baseline_turns)
    print '{0:<36} {1:^5.3f}'.format('Total proposed speech time:', proposed_total)
    print '{0:<36} {1}'.format('Total proposed turns:', proposed_turns)
    print '{0:<36} {1:^5.3f}'.format('Average proposed turn time:',
            proposed_total/proposed_turns)
    incorrect = noise + missed
    print '{0:<36} {1:^5.3f}'.format('Incorrect time:', incorrect)
    correct = baseline_total - incorrect
    print '{0:<36} {1:^5.3f}'.format('Correct time:', correct)
    print '{0:<36} {1}'.format('VAD Error Rate:', incorrect / baseline_total)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rate a Voice Activity \
            Detection recipe against a baseline recipe to ensure all real \
            speech parts are inside VAD detected speech parts.')
    parser.add_argument('baseline', type=str,
                    help='Especifies the baseline recipe file.')
    parser.add_argument('proposed', type=str,
                    help='Especifies the proposed recipe file, to benchmark.')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout, \
                    help='Especifies an output file, default stdout.')
    parser.add_argument('-t', dest='threshold', type=float, default=0.25,
                    help='Especifies threshold to determine when a time is \
                    incorrect, defaults to 0.25 seconds before-after.')
    parser.add_argument('-sn', action='store_true',
                    help='If set, shows each speech as noise time interval')
    parser.add_argument('-ns', action='store_true',
                    help='If set, shows each noise as speech time interval')
    args = parser.parse_args()

    # Process arguments
    print 'Reading baseline recipe from:', args.baseline
    with open(args.baseline, 'r') as recfile:
        parsed_baseline, totalb = parse_recipe(recfile)
    print 'Reading proposed recipe from:', args.proposed
    with open(args.proposed, 'r') as recfile:
        parsed_proposed, totalp = parse_recipe(recfile)
    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    print 'Threshold:', args.threshold
    threshold = args.threshold

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            benchmark(parsed_baseline, parsed_proposed, threshold, outf)
    else:
        benchmark(parsed_baseline, parsed_proposed, threshold, outfile)

