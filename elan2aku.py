#!/usr/bin/python2
import argparse
import sys
from lxml import etree


def write_recipe(efile, outf):
    """Write output recipe"""
    lna_letter = 'a_'
    lna_number = 1
    tree = etree.parse(efile)
    root = tree.getroot()
    audio = root.find('HEADER').find('MEDIA_DESCRIPTOR').attrib['MEDIA_URL'][7:]
    times = root.find('TIME_ORDER').findall('TIME_SLOT')
    annotations = root.find('TIER').findall('ANNOTATION')
    for a in annotations:
        a2 = a.find('ALIGNABLE_ANNOTATION')
        t1 = times[int(a2.attrib['TIME_SLOT_REF1'][2:]) - 1].attrib['TIME_VALUE']
        t2 = times[int(a2.attrib['TIME_SLOT_REF2'][2:]) - 1].attrib['TIME_VALUE']
        outline = 'audio=' + audio +\
                  ' lna=' + lna_letter + str(lna_number) +\
                  ' start-time=' + str(float(t1) / 1000.0) +\
                  ' end-time=' + str(float(t2) / 1000.0)
        speaker = a2.find('ANNOTATION_VALUE')
        if speaker is not None:
            outline += ' speaker=' + speaker.text
        outline += '\n'
        outf.write(outline)
        lna_number += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts an Elan file to \
                                     AKU recipe.')
    parser.add_argument('efile', type=str,
                        help='Specifies the input Elan file')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout,
                        help='Specifies an output recipe file, default stdout.')
    args = parser.parse_args()

    # Process arguments
    print 'Reading Elan file from:', args.efile

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
            write_recipe(args.efile, outf)
    else:
        write_recipe(args.efile, outfile)
