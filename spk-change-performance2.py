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
    speaker_name = re.compile('speaker=(\S+)')
    this_file = ''
    total_entries = 0
    for line in rfile:
        try:
            audio = audio_file.search(line).groups()[0]
            start = float(start_time.search(line).groups()[0])
            end = float(end_time.search(line).groups()[0])
            try:
                speaker = speaker_name.search(line).groups()[0]
            except AttributeError:
                speaker = ''
            if audio != this_file:
                if this_file != '':
                    r.append((audio, rr))
                    rr = []
                this_file = audio
            rr.append((start, end, speaker))
            total_entries += 1
        except AttributeError:
            print 'Recipe line without recognizable data:'
            print line
    # Append last audio file
    r.append((this_file, rr))
    return r, total_entries

def aprox(n1, n2, thresh):
    """Determines if two values are "close enough" according to a threshold"""
    if n2 >= n1-thresh and n2 <= n1+thresh:
        return True
    return False

def _nearest_diff(n1, dlist):
    """Returns the absolute difference of n1 with the nearest value in dlist."""
    nearest = sys.maxint
    mindiff = sys.maxint
    for n2 in dlist:
        t = abs(n1 - n2)
        if t < mindiff:
            mindiff = t
            nearest = n2
    return mindiff, nearest

def get_changing_times(recipe):
    """Gets a parsed recipe, returns a list of speaker change times for each file
    (no start-end differentiations, no speaker data)"""
    r = []
    rr = []
    count = 0
    for i in recipe:
        for j in i[1]:
            rr.append(j[0])
            rr.append(j[1])
            count += 2
        r.append((i[0], rr))
        rr = []
    return r, count

def get_changing_times2(recfile):
    """Returns a list of starting and a list of ending times."""
    times = recfile[0][1]
    startings = [t[0] for t in times]
    endings = [t[1] for t in times]
    return startings, endings


def benchmark2(baseline, proposed, outf):
    bstartings, bendings = get_changing_times2(baseline)
    pstartings, pendings = get_changing_times2(proposed)
    start_diff = 0.0
    missing_starts = 0
    end_diff = 0.0
    missing_ends = 0
    for start in bstartings:
        t, nearest = _nearest_diff(start, pstartings)
        if t > threshold:
            # print start, nearest
            start_diff += t
            missing_starts += 1
    for end in bendings:
        t, nearest = _nearest_diff(end, pendings)
        if t > threshold:
            # print end, nearest
            end_diff += t
            missing_ends += 1

    print "Total start_diff:", start_diff
    print "Missing starts:", missing_starts
    print "Total end_diff:", end_diff
    print "Missing ends:", missing_ends
    total_starts = len(bstartings)
    total_ends = len(bendings)
    total_turns = total_starts + total_ends
    print "Total turns:", total_turns
    print "Total diff:", start_diff + end_diff
    total_missed = missing_starts + missing_ends
    print "Missed turn ratio:", total_missed / float(total_turns)


def benchmark(baseline, proposed, outf):
    """Benchmarks proposed changing points agains baseline ones."""
    global total_timesb, total_timesp
    countb = 0
    countbs = 0
    countbe = 0
    countr = 0
    correct = 0
    insertions = 0
    deletions = 0
    substitutions = 0
    corrects = 0
    insertionss = 0
    deletionss = 0
    substitutionss = 0
    correcte = 0
    insertionse = 0
    deletionse = 0
    substitutionse = 0
    times_baseline, total_timesb = get_changing_times(baseline)
    times_proposed, total_timesp = get_changing_times(proposed)
    # Composite benchmark, very inneficient to do them separately...
    for files in xrange(len(times_baseline)):
        # Both have same audio files, so same number of entries
        while countr < len(times_proposed[files][1]):
            time = times_proposed[files][1][countr]
            countr += 1
            while countb < len(times_baseline[files][1]):
                btime = times_baseline[files][1][countb]
                if aprox(time, btime, threshold):
                    if args.sc:
                        print 'Correct time:', btime, 'proposed:',  time
                    correct += 1
                    countb += 1
                    break
                elif btime < time:
                    if args.sd:
                        print 'Time deletion:', btime, 'proposed:', time
                    deletions += 1
                elif btime > time:
                    if args.si:
                        print 'Time insertion:', btime, 'proposed:', time
                    insertions += 1
                    break
                countb += 1
            else:
                if args.si:
                    print 'Time insertion:', 0, 'proposed:', time
                insertions += 1
    countr = 0
    for files in xrange(len(baseline)):
        #Both have same audio files, so same number of entries
        while countr < len(proposed[files][1]):
            start = proposed[files][1][countr][0]
            end = proposed[files][1][countr][1]
            countr += 1
            while countbs < len(baseline[files][1]):
                bstart = baseline[files][1][countbs][0]
                if aprox(start, bstart, threshold):
                    if args.sc:
                        print 'Correct start:', bstart, 'proposed:',  start
                    corrects += 1
                    countbs += 1
                    break
                elif bstart < start:
                    if args.sd:
                        print 'Start deletion:', bstart, 'proposed:', start
                    deletionss += 1
                elif bstart > start:
                    if args.si:
                        print 'Start insertion:', bstart, 'proposed:', start
                    insertionss += 1
                    break
                countbs += 1
            else:
                if args.si:
                    print 'Start insertion:', 0, 'proposed:', start
                insertionss += 1
            while countbe < len(baseline[files][1]):
                bend = baseline[files][1][countbe][1]
                if aprox(end, bend, threshold):
                    if args.sc:
                        print 'Correct end:', bend, 'proposed:', end
                    correcte += 1
                    countbe += 1
                    break
                elif bend < end:
                    if args.sd:
                        print 'End deletion:', bend, 'proposed:', end
                    deletionse += 1
                elif bend > end:
                    if args.si:
                        print 'End insertion:', bend, 'proposed:', end
                    insertionse += 1
                    break
                countbe += 1
            else:
                if args.si:
                    print 'End insertion:', 0, 'proposed:', end
                insertionse += 1
    base, propos = get_stats(baseline, proposed)
    print_results((float(correct), float(corrects), float(correcte)),
                (insertions, insertionss, insertionse),
                (deletions, deletionss, deletionse),
                (substitutions, substitutionss, substitutionse),
                (base, propos))

def get_stats(baseline, proposed):
    """Get useful stats comparing baseline and proposed data"""
    global total_segment_durationsb, total_segment_durationsp, \
            max_segment_durationb, max_segment_durationp, \
            min_segment_durationb, min_segment_durationp
    for entry in baseline:
        for segment in entry[1]:
            this_seg = segment[1] - segment[0]
            if this_seg > max_segment_durationb:
                max_segment_durationb = this_seg
            if this_seg < min_segment_durationb or min_segment_durationb == 0.0:
                min_segment_durationb = this_seg
            total_segment_durationsb += this_seg
    for entry in proposed:
        for segment in entry[1]:
            this_seg = segment[1] - segment[0]
            if this_seg > max_segment_durationp:
                max_segment_durationp = this_seg
            if this_seg < min_segment_durationp or min_segment_durationp == 0.0:
                min_segment_durationp = this_seg
            total_segment_durationsp += this_seg
    return (total_segment_durationsb, max_segment_durationb, min_segment_durationb), \
            (total_segment_durationsp, max_segment_durationp, min_segment_durationp)

def print_results(correct, insertions, deletions, substitutions, stats):
    """Pretty print useful results"""
    precision = correct[0]/(correct[0] + insertions[0])
    start_precision = correct[1]/(correct[1] + insertions[1])
    end_precision = correct[2]/(correct[2] + insertions[2])
    recall = correct[0]/(correct[0] + deletions[0])
    start_recall = correct[1]/(correct[1] + deletions[1])
    end_recall = correct[2]/(correct[2] + deletions[2])
    f1 = 2*(precision*recall/(precision+recall))
    start_f1 = 2*(start_precision*start_recall/(start_precision+start_recall))
    end_f1 = 2*(end_precision*end_recall/(end_precision+end_recall))
    print '{0:>58}'.format('Benchmark results:          ')
    print '{0:>58}'.format('------------------          ')

    print '{0:<36} {1:^5}'.format('Correct:', int(correct[0]))
    print '{0:<36} {1:^5}'.format('Inserted:', int(insertions[0]))
    print '{0:<36} {1:^5}'.format('Deleted:', int(deletions[0]))
    print '{0:<36} {1:^5}'.format('Substituted:', int(substitutions[0]))
    print '{0:<36} {1:^5.3f}'.format('Accuracy:', correct[0]/total_timesb)
    print '{0:<36} {1:^5.3f}'.format('Precision:', precision)
    print '{0:<36} {1:^5.3f}'.format('Recall:', recall)
    print '{0:<36} {1:^5.3f}'.format('F1:', f1)

    print ''
    print '{0:>58}'.format('Detailed results:           ')
    print '{0:>58}'.format('-----------------           ')
    print '{0:>58}'.format('Start points                 End points')
    print '{0:>58}'.format('---------------------------------------')
    print '{0:<23} {1:^5}          -           {2:^5}'.format('Correct:', \
            int(correct[1]), int(correct[2]))
    print '{0:<23} {1:^5}          -           {2:^5}'.format('Inserted:', \
            int(insertions[1]), int(insertions[2]))
    print '{0:<23} {1:^5}          -           {2:^5}'.format('Deleted:', \
            int(deletions[1]), int(deletions[2]))
    print '{0:<23} {1:^5}          -           {2:^5}'.format('Substituted:', \
            int(substitutions[1]), int(substitutions[2]))
    print '{0:<23} {1:^5.3f}          -           {2:^5.3f}'.format('Accuracy:', \
            correct[1]/totalb, correct[2]/totalb)
    print '{0:<23} {1:^5.3f}          -           {2:^5.3f}'.format('Precision:', \
            start_precision, end_precision)
    print '{0:<23} {1:^5.3f}          -           {2:^5.3f}'.format('Recall:', \
            start_recall, end_recall)
    print '{0:<23} {1:^5.3f}          -           {2:^5.3f}'.format('F1:', \
            start_f1, end_f1)

    print ''
    print '{0:>56}'.format('Segment stats (seconds):    ')
    print '{0:>56}'.format('------------------------    ')
    print '{0:>56}'.format('Baseline                 Proposed')
    print '{0:>56}'.format('---------------------------------')
    print '{0:<23} {1:>5.2f}          -           {2:>5.2f}'.format('Average duration:', \
            stats[0][0]/totalb, stats[1][0]/totalp)
    print '{0:<23} {1:>5.2f}          -           {2:>5.2f}'.format('Maximum duration:', \
            stats[0][1], stats[1][1])
    print '{0:<23} {1:>5.2f}          -           {2:>5.2f}'.format('Minimum duration:', \
            stats[0][2], stats[1][2])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rate a recipe against \
                    another, typically to benchmark diarization performance.')
    parser.add_argument('baseline', type=str,
                    help='Especifies the baseline recipe file.')
    parser.add_argument('proposed', type=str,
                    help='Especifies the proposed recipe file, to benchmark.')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout, \
                    help='Especifies an output file, default stdout.')
    parser.add_argument('-t', dest='threshold', type=float, default=0.25,
                    help='Especifies threshold to determine when a time is \
                    incorrect, default 0.25 seconds before-after.')
    parser.add_argument('-sc', action='store_true',
                    help='If set, shows the time of each correct')
    parser.add_argument('-si', action='store_true',
                    help='If set, shows the time of each insertion')
    parser.add_argument('-sd', action='store_true',
                    help='If set, shows the time of each deletion')
    parser.add_argument('-ss', action='store_true',
                    help='If set, shows the time of each substitution')
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

    # Useful for stats:
    total_segment_durationsb = 0.0
    max_segment_durationb = 0.0
    min_segment_durationb = 0.0
    total_segment_durationsp = 0.0
    max_segment_durationp = 0.0
    min_segment_durationp = 0.0
    total_timesb = 0
    total_timesp = 0

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            benchmark2(parsed_baseline, parsed_proposed, outf)
    else:
        benchmark2(parsed_baseline, parsed_proposed, outfile)
