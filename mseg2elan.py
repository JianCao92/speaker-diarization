#!/usr/bin/python2
import argparse
import sys
from lxml import etree
from datetime import datetime
from mimetypes import guess_type


def dateIso():
    """ Returns the actual date in the format expected by ELAN. Source:
        http://stackoverflow.com/questions/3401428/how-to-get-an-isoformat-datetime-string-including-the-default-timezone"""
    dtnow = datetime.now()
    dtutcnow = datetime.utcnow()
    delta = dtnow - dtutcnow
    hh, mm = divmod((delta.days * 24 * 60 * 60 + delta.seconds + 30) // 60, 60)
    return '%s%+02d:%02d' % (dtnow.isoformat(), hh, mm)


def parse_mseg(rfile):
    """Parses input mseg file"""
    r = []
    # Read filename
    r.append(rfile.readline()[1:-1])
    for line in rfile:
        # Convert to milliseconds in string format
        r.append(str(int(float(line[:-1]) * 1000)))
    return r


def write_elan(rfile, outf):
    """Write Elan file"""
    ts_count = 1
    an_count = 1
    NS = 'http://www.w3.org/2001/XMLSchema-instance'
    location_attr = '{%s}noNamespaceSchemaLocation' % NS
    doc = etree.Element('ANNOTATION_DOCUMENT',
                        attrib={location_attr: 'http://www.mpi.nl/tools/elan/EAFv2.7.xsd',
                                'AUTHOR': '', 'DATE': dateIso(),
                                'FORMAT': '2.7', 'VERSION': '2.7'})
    header = etree.SubElement(doc, 'HEADER',
                              attrib={'MEDIA_FILE': '',
                                      'TIME_UNITS': 'milliseconds'})
    etree.SubElement(header, 'MEDIA_DESCRIPTOR',
                     attrib={'MEDIA_URL': 'file://' + rfile[0],
                             'MIME_TYPE': guess_type(rfile[0])[0],
                             'RELATIVE_MEDIA_URL': ''})
    t = etree.SubElement(header, 'PROPERTY',
                         attrib={'NAME': 'lastUsedAnnotationId'})
    t.text = str(len(rfile) - 1)
    time = etree.SubElement(doc, 'TIME_ORDER')
    for line in rfile[1:]:
        etree.SubElement(time, 'TIME_SLOT',
                         attrib={'TIME_SLOT_ID': 'ts' + str(ts_count),
                                 'TIME_VALUE': line})
        ts_count += 1
    tier = etree.SubElement(doc, 'TIER',
                            attrib={'DEFAULT_LOCALE': 'en',
                                    'LINGUISTIC_TYPE_REF': 'default-lt',
                                    'TIER_ID': 'Speakers'})
    for line in rfile[1:-1]:
        a = etree.SubElement(tier, 'ANNOTATION')
        etree.SubElement(a, 'ALIGNABLE_ANNOTATION',
                         attrib={'ANNOTATION_ID': 'a' + str(an_count),
                                 'TIME_SLOT_REF1': 'ts' + str(an_count),
                                 'TIME_SLOT_REF2': 'ts' + str(an_count + 1)})
        an_count += 1

    etree.SubElement(doc, 'LINGUISTIC_TYPE',
                     attrib={'GRAPHIC_REFERENCES': 'false',
                             'LINGUISTIC_TYPE_ID': 'default-lt',
                             'TIME_ALIGNABLE': 'true'})
    etree.SubElement(doc, 'LOCALE',
                     attrib={'COUNTRY_CODE': 'US',
                             'LANGUAGE_CODE': 'en'})

    tree = etree.ElementTree(doc)
    tree.write(outf, pretty_print=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts mseg output to \
                                     Elan format.')
    parser.add_argument('msfile', type=str,
                        help='Specifies the input mseg file')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout,
                        help='Specifies an output file, default stdout.')
    args = parser.parse_args()

    # Process arguments
    print 'Reading mseg file from:', args.msfile
    with open(args.msfile, 'r') as msfile:
        parsed_mseg = parse_mseg(msfile)

    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    # End of argument processing

    # Do the real work
    write_elan(parsed_mseg, outfile)
