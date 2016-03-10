#!/usr/bin/python2
import argparse
import sys


def parse_log(lfile):
    """Parses input log"""
    dur_time = 0.0
    header = lfile.readline()
    header += lfile.readline()
    header += lfile.readline()
    header += lfile.readline()
    text = ''
    while True:
        line = lfile.readline()
        if not line:
            break
        if line in header:
            continue
        line = line.split()
        if line[0] == 'LNA:':
            continue  # Skip LNAs
        elif line[0] == 'REC:':
            for w in line[1:]:
                text += w + ' '
        elif line[0] == 'DUR:':
            dur_time += float(line[1][:-1])
        else:
            print 'Log line without recognizable line'
            print line
    return header, text, dur_time


def write_log(header, lna_name, text, dur, outf):
    outf.write(header)
    outf.write('LNA: ' + lna_name + '\n')
    outf.write('REC: ' + text + '\n')
    outf.write('DUR: ' + str(dur) + 's\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates a version of a log \
                suitable for comparison with the baseline one on sclite.')
    parser.add_argument('logfile', type=str,
                        help='Especifies the log file')
    parser.add_argument('lna', type=str,
                        help='Especifies baseline LNA name')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout,
                        help='Especifies an output file, default stdout.')
    args = parser.parse_args()

    # Process arguments
    print 'Reading log from:', args.logfile
    with open(args.logfile, 'r') as logfile:
        header, text, dur = parse_log(logfile)

    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            write_log(header, args.lna, text, dur, outf)
    else:
        write_log(header, args.lna, text, dur, outfile)
