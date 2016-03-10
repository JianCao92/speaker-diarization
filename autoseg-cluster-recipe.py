#!/usr/bin/python2
import argparse
import sys
import re

def parse_recipe(rfile):
    """Parses input recipe, checks for LNA's"""
    r = []
    audio_file = re.compile('audio=(\S+)')
    lna_name = re.compile('lna=(\S+)')
    start_time = re.compile('start-time=(\d+.\d+)')
    end_time = re.compile('end-time=(\d+.\d+)')
    for line in rfile:
        try:
            audio = audio_file.search(line).groups()[0]
            lna = lna_name.search(line).groups()[0]
            start = float(start_time.search(line).groups()[0])
            end = float(end_time.search(line).groups()[0])
            r.append((audio, lna, start, end))
        except AttributeError:
            print 'Recipe line without recognizable times:'
            print line
    return r

def read_clustering(cfile):
    """Parses clustering information, check's speaker names"""
    r = []
    target = re.compile('speaker: (\S+)')
    for line in cfile:
        try:
            r.append(target.search(line).groups()[0])
        except AttributeError:
            pass
    return r


def write_recipe_line(recline, spk_name, outf):
    outf.write('audio='+recline[0]+\
            ' lna='+recline[1]+\
            ' start-time='+str(recline[2])+\
            ' end-time='+str(recline[3])+\
            ' speaker='+spk_name+'\n')

def write_recipe(rfile, cfile, outf):
    for i in xrange(len(rfile)):
        write_recipe_line(rfile[i], cfile[i], outf)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Correct speaker names from an\
                        automatically segmented recipe, with the output of the\
                        automatic clustering.')
    parser.add_argument('segfile', type=str,
                    help='Especifies the input segmentation file')
    parser.add_argument('clusfile', type=str,
                    help='Especifies the input clustering file')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout, \
                    help='Especifies an output file, default stdout.')
    args = parser.parse_args()

    # Process arguments
    print 'Reading segmentation recipe from:', args.segfile
    with open(args.segfile, 'r') as segfile:
        seg_recipe = parse_recipe(segfile)
    print 'Reading clustering from:', args.clusfile
    with open(args.clusfile, 'r') as clusfile:
        clus_file = read_clustering(clusfile)

    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            write_recipe(seg_recipe, clus_file, outf)
    else:
        write_recipe(seg_recipe, clus_file, outfile)

