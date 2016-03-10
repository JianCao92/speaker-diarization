#!/usr/bin/python2
import argparse
import sys
import re
import os


def parse_recipe(rfile):
    """Parses input recipe, checks for LNA's"""
    r = []
    audio_file = re.compile('audio=(\S+)')
    lna_name = re.compile('lna=(\S+)')
    start_time = re.compile('start-time=(\d+.\d+)')
    end_time = re.compile('end-time=(\d+.\d+)')
    speaker_name = re.compile('speaker=(\S+)')
    for line in rfile:
        try:
            audio = audio_file.search(line).groups()[0]
            lna = lna_name.search(line).groups()[0]
            start = float(start_time.search(line).groups()[0])
            end = float(end_time.search(line).groups()[0])
            speaker = speaker_name.search(line).groups()[0]
            r.append((audio, lna, start, end, speaker))
        except AttributeError:
            print 'Recipe line without recognizable times:'
            print line
    return r


def write_recipe_line(recline, spath, outf):
    lna = recline[1]
    alignment = ' alignment=' + spath + lna + '.seg'
    outf.write('audio=' + recline[0] +
               alignment +
               ' lna=' + recline[1] +
               ' start-time=' + str(recline[2]) +
               ' end-time=' + str(recline[3]) +
               ' speaker=' + recline[4] + '\n')


def write_recipe(recipe, spath, outf):
    for l in recipe:
        write_recipe_line(l, spath, outf)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add segmentation path to a \
                                     recipe.')
    parser.add_argument('recfile', type=str,
                        help='Especifies the input recipe file')
    parser.add_argument('segpath', type=str,
                        help='Especifies the seg files path.')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout,
                        help='Especifies an output file, default stdout.')
    args = parser.parse_args()

    # Process arguments
    print 'Reading recipe from:', args.recfile
    with open(args.recfile, 'r') as recfile:
        recipe = parse_recipe(recfile)
    print 'Segmentation files path set to:', args.segpath
    segpath = args.segpath
    if segpath[-1] != '/':
        segpath += '/'
    if not os.path.isdir(segpath):
        print 'Error,', segpath, 'is not a valid directory'
        exit()

    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            write_recipe(recipe, segpath, outf)
    else:
        write_recipe(recipe, segpath, outfile)
