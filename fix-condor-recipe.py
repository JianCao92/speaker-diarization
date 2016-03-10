#!/usr/bin/python2
import argparse
import sys
import re

def parse_recipe(rfile):
    """Parses input recipe to get LNA order"""
    r = []
    lna_name = re.compile('lna=(\S+)')
    for line in rfile:
        try:
            lna = lna_name.search(line).groups()[0]
            r.append(lna)
        except AttributeError:
            print 'Recipe line without recognizable LNA:'
            print line
    return r

def parse_log(lfile):
    """Parses input log"""
    r = []
    lna_name = re.compile('LNA: (\S+)')
    header = lfile.readline()
    header += lfile.readline()
    header += lfile.readline()
    header += lfile.readline()
    while True:
        lna_text = lfile.readline()
        if not lna_text:
            break
        if lna_text in header:
            continue
        try:
            lna = lna_name.search(lna_text).groups()[0]
        except AttributeError:
            print 'Log line without recognizable LNA:'
            print lna_text
        lna_text += lfile.readline()
        lna_text += lfile.readline()
        r.append((lna, lna_text))
    return header, r

def write_log_line(logline, outf):
    outf.write(logline[1])

def write_log(rec, log, header, outf):
    outf.write(header)
    for i in rec:
        for j in log:
            if j[0] == i:
                write_log_line(j, outf)
                break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Correct speaker order from a\
                        condor processed logfile, to match that of a recipe.\
                        Useful for sc_stats.')
    parser.add_argument('recfile', type=str,
                    help='Especifies the recipe file')
    parser.add_argument('logfile', type=str,
                    help='Especifies the log file')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout, \
                    help='Especifies an output file, default stdout.')
    args = parser.parse_args()

    # Process arguments
    print 'Reading recipe from:', args.recfile
    with open(args.recfile, 'r') as recfile:
        recipe = parse_recipe(recfile)
    print 'Reading log from:', args.logfile
    with open(args.logfile, 'r') as logfile:
        header, log = parse_log(logfile)

    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            write_log(recipe, log, header, outf)
    else:
        write_log(recipe, log, header, outfile)

