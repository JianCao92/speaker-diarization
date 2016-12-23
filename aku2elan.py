#!/usr/bin/python2
import argparse
import sys
import re
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
            print 'Recipe line without recognizable data:'
            print line
    return r


def write_elan(recipe, outf):
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
                     attrib={'MEDIA_URL': 'file://' + recipe[0][0],
                             'MIME_TYPE': guess_type(recipe[0][0])[0],
                             'RELATIVE_MEDIA_URL': ''})
    t = etree.SubElement(header, 'PROPERTY',
                         attrib={'NAME': 'lastUsedAnnotationId'})
    t.text = str(len(recipe))
    time = etree.SubElement(doc, 'TIME_ORDER')
    for line in recipe:
        etree.SubElement(time, 'TIME_SLOT',
                         attrib={'TIME_SLOT_ID': 'ts' + str(ts_count),
                                 'TIME_VALUE': str(int(line[2] * 1000))})
        ts_count += 1
        etree.SubElement(time, 'TIME_SLOT',
                         attrib={'TIME_SLOT_ID': 'ts' + str(ts_count),
                                 'TIME_VALUE': str(int(line[3] * 1000))})
        ts_count += 1
    tier = etree.SubElement(doc, 'TIER',
                            attrib={'DEFAULT_LOCALE': 'en',
                                    'LINGUISTIC_TYPE_REF': 'default-lt',
                                    'TIER_ID': 'Speakers'})
    for line in recipe:
        a = etree.SubElement(tier, 'ANNOTATION')
        a2 = etree.SubElement(a, 'ALIGNABLE_ANNOTATION',
                              attrib={'ANNOTATION_ID': 'a' + str(an_count),
                                      'TIME_SLOT_REF1': 'ts' + str(an_count * 2 - 1),
                                      'TIME_SLOT_REF2': 'ts' + str(an_count * 2)})
        if line[4]:
            a3 = etree.SubElement(a2, 'ANNOTATION_VALUE')
            a3.text = line[4]
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
    parser = argparse.ArgumentParser(description='Converts an AKU recipe to \
                                     Elan format.')
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
    write_elan(parsed_recipe, outfile)
