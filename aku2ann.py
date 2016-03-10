#!/usr/bin/python2
import argparse
import sys
import re


def parse_recipe(rfile):
    """Parses input recipe"""
    r = []
    audio_file = re.compile('audio=(\S+)')
    lna_name = re.compile('lna=(\S+)')
    start_time = re.compile('start-time=(\d+.\d+)')
    end_time = re.compile('end-time=(\d+.\d+)')
    speaker_tag = re.compile('speaker=(\S+)')
    for line in rfile:
        try:
            audio = audio_file.search(line).groups()[0]
            lna = lna_name.search(line).groups()[0]
            start = float(start_time.search(line).groups()[0])
            end = float(end_time.search(line).groups()[0])
            try:
                speaker = speaker_tag.search(line).groups()[0]
            except AttributeError:
                speaker = ''
            r.append((audio, lna, start, end, speaker))
        except AttributeError:
            print 'Recipe line without recognizable data:', line
    return r


def write_ann(recipe, outf):
    """Write ann (simple annotation) file"""
    audio = ''
    for line in recipe:
        if audio != line[0]:
            audio = line[0]
            outf.write('# ' + audio + '\n')
        outf.write(str(line[2]) + '\t' + str(line[3]) + '\t' + line[4] + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts an AKU recipe to \
                                     simple annotation format.')
    parser.add_argument('recfile', type=str,
                        help='Specifies the input recipe file')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout,
                        help='Specifies an output file, default stdout.')
    args = parser.parse_args()

    # Process arguments
    print 'Reading recipe from:', args.recfile
    with open(args.recfile, 'r') as recfile:
        parsed_recipe = parse_recipe(recfile)

    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    # End of argument processing

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            write_ann(parsed_recipe, outf)
    else:
        write_ann(parsed_recipe, outfile)
