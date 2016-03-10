#!/usr/bin/env python2
import argparse
import sys
import re
from itertools import izip
from operator import itemgetter
from pprint import pprint

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


def get_changing_times2(recfile):
    """Return a list of starting and a list of ending times."""
    times = recfile[0][1]
    speakers = None
    startings = [t[0] for t in times]
    endings = [t[1] for t in times]
    if len(times[0]) == 3:  # We have speaker info
        speakers = [t[2] for t in times]
    return startings, endings, speakers


def _generate_labeled_list(input_lst, resolution):
    """Generate a list of None (silence) or spk_label.

    Per-resolution in seconds. So if resolution is 1, returns list of one
    spk_label per second.

    Input_lst is [(start, end, spk_label), ...]
    """
    def _gen_time(start, end, label):
        """Generate (end - start)/resolution labels, per resolution required."""
        total_labels = (end - start) / resolution
        return [label] * int(total_labels)
    result = []
    current_time = 0.0
    for start, end, label in input_lst:
        if start > current_time:  # Generate silence
            result.extend(_gen_time(current_time, start, None))
        result.extend(_gen_time(start, end, label))
        current_time = end
    return result


def benchmark(baseline, proposed, resolution, outf):
    baseline_l = _generate_labeled_list(baseline[0][1], resolution)
    proposed_l = _generate_labeled_list(proposed[0][1], resolution)
    correct_time = 0.0
    incorrect_time = 0.0

    matches = {}

    for baseline, proposed in izip(baseline_l, proposed_l):
        matches.setdefault(baseline, {}).setdefault(proposed, 0)
        matches[baseline][proposed] += 1

    ordered_matches = sorted(((k, vv, matches[k][vv])
                             for k, v in matches.iteritems() for vv in v),
                             key=itemgetter(2), reverse=True)

    best_match = {}
    for match in ordered_matches:
        if match[0] not in best_match:
            best_match[match[0]] = match[1]

    # pprint(best_match)

    for baseline, proposed in izip(baseline_l, proposed_l):
        if best_match[baseline] == proposed:
            correct_time += 1
        else:
            incorrect_time += 1

    print 'Correct time:', correct_time * resolution
    print 'Incorrect time:', incorrect_time * resolution
    print 'Total time:', (incorrect_time + correct_time) * resolution
    print 'DER:', incorrect_time / (incorrect_time + correct_time)


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

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            benchmark(parsed_baseline, parsed_proposed, 0.001, outf)
    else:
        benchmark(parsed_baseline, parsed_proposed, 0.001, outfile)
