#!/usr/bin/python2
import argparse
import sys
import re

def parse_recipe(rfile, spk):
    spk_time = {}
    t1 = 0.0
    t2 = 0.0
    speaker = spk
    spk_name = re.compile('speaker=(\S+)')
    start_time = re.compile('start-time=(\d+.\d+)')
    end_time = re.compile('end-time=(\d+.\d+)')
    for line in rfile:
        try:
            if spk != None:
                if spk_name.search(line).groups()[0] != spk:
                    # Another speaker, skipt it
                    continue
            else:
                speaker = spk_name.search(line).groups()[0]
            # Calculate time and add it to the total
            t1 = float(start_time.search(line).groups()[0])
            t2 = float(end_time.search(line).groups()[0])
            spk_time[speaker] = spk_time.get(speaker, 0) + t2-t1
        except AttributeError:
            print 'Recipe line without recognizable times:'
            print line
    return spk_time

def write_log(r, outf):
    total = 0
    longest = 0
    shortest = sys.maxint
    outf.write('Results:\n')
    outf.write('========\n')
    outf.write('Recipe file: '+args.recfile+'\n')
    print 'Calculated speaker times:'
    for i in sorted(r, key=r.get, reverse=True):
        print 'Speaker:', i, '- Time:', r[i]
        total += r[i]
        if r[i] > longest:
            longest = r[i]
        if r[i] < shortest:
            shortest = r[i]
    print 'Total speakers:', len(r)
    print 'Total time:', total
    print 'Average speaker time:', total/len(r)
    print 'Most frequent speaker time:', longest, 'percentage:', (longest/total)*100
    print 'Less frequent speaker time:', shortest, 'percentage:', (shortest/total)*100

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculate speaking time')
    parser.add_argument('recfile', type=str,
                    help='Especifies the recipe file')
    parser.add_argument('-s', dest='speaker',
                    type=str, default=None,
                    help="Especifies speaker to sum it's time, default None \
                    (calculate the speaking time of everyone)")
    parser.add_argument('-o', dest='outfile',
                    type=str, default=sys.stdout,
                    help='Especifies an output file, default stdout')
    args = parser.parse_args()

    print 'Reading recipe from:', args.recfile
    recfile = open(args.recfile, 'r')

    if args.speaker != None:
        print 'Calculating', args.speaker, 'speaking time'
    else:
        print 'Calculating speaking time'

    if args.outfile != sys.stdout:
        outfile = open(args.outfile, 'w')
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    result = parse_recipe(recfile, args.speaker)

    write_log(result, outfile)

    recfile.close()
    outfile.close()

