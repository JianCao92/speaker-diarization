#!/usr/bin/python2
import argparse
import sys
import os
import re


def parse_recipe(rfile):
    """Parses input recipe, checks for WAV's"""
    r = []
    audio_file = re.compile('audio=(\S+)')
    for line in rfile:
        try:
            audio = audio_file.search(line).groups()[0]
            r.append(audio)
        except AttributeError:
            print 'Recipe line without recognizable audio files:'
            print line
    return r


def wav_to_exp(wavfile, epath):
    """Converts .wav filename into the asociated .exp file"""
    expfile = epath
    expfile += os.path.splitext(os.path.basename(wavfile))[0]
    expfile += '.exp'
    if not os.path.isfile(expfile):
        print 'Error,', expfile, 'does not exist'
        exit()
    return expfile


def inc_lna(lna):
    """Generate suitable lna names"""
    for c in xrange(len(lna) - 1, -1, -1):
        if lna[c] != 'z':
            lna = lna[0:c] + chr(ord(lna[c]) + 1) + 'a' * (len(lna) - c - 1)
            break
    else:
        lna = 'a' * (len(lna) + 1)
    return lna


def parse_exp_file(expfile, lna):
    """Return the proper speech-nonspeech turns with a suitable lna name"""
    t = []
    lnacount = 1
    linecount = 0.0
    start = 0
    end = 0
    in_speech = False
    in_speech_silence_count = 0
    in_silence_speech_count = 0
    rline = None
    with open(expfile, 'r') as efile:
        for line in efile:
            if '<w>' in line and not in_speech:
                if in_silence_speech_count > 0:
                    in_silence_speech_count -= 1
                else:
                    rline = None
                linecount += 1
                continue
            elif 'p' in line and in_speech:
                if in_speech_silence_count > 0:
                    in_speech_silence_count -= 1
                else:
                    rline = None
                linecount += 1
                continue
            elif 'p' in line and not in_speech:
                in_silence_speech_count += 1
                if not rline:
                    rline = linecount
                if in_silence_speech_count / rate < ms:
                    linecount += 1
                    continue
                in_speech = True
                in_silence_speech_count = 0
                start = rline / rate - sbe
                rline = None
                linecount += 1
                continue
            elif '<w>' in line and in_speech:
                in_speech_silence_count += 1
                if not rline:
                    rline = linecount
                if in_speech_silence_count / rate < mns:
                    linecount += 1
                    continue
                in_speech = False
                in_speech_silence_count = 0
                end = rline / rate + see
                rline = None
                t.append((lna + '_' + str(lnacount), start, end))
                start = None
                linecount += 1
                lnacount += 1
        if start:
            # One turn started but it hasn't ended, write it as last turn
            # if it's bigger than ms
            end = (linecount - 1) / rate
            if end - start >= ms:
                end += see
                t.append((lna + '_' + str(lnacount), start, end))
    return t


def write_recipe_line(wav, lna, start, end, outf):
    """Write output recipes"""
    outf.write('audio=' + wav +
               ' lna=' + lna +
               ' start-time=' + str(start) +
               ' end-time=' + str(end) + '\n')


def write_recipe(rec, epath, outf):
    lna = 'a'  # Lna base name for the next recipe line
    for wav in rec:
        turns = parse_exp_file(wav_to_exp(wav, epath), lna)
        for t in turns:
            write_recipe_line(wav, t[0], t[1], t[2], outf)
        lna = inc_lna(lna)  # Increment Lna base name for the following recipe line


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates a recipe from the \
                        Speech Activity Detection classify_speecon output, \
                        (.exp files) that is, speech/non-speech turn detection')
    parser.add_argument('recfile', type=str,
                        help='Specifies the input recipe file')
    parser.add_argument('exppath', type=str,
                        help='Specifies the input .exp files path')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout,
                        help='Specifies an output file, default stdout.')
    parser.add_argument('-r', dest='rate', type=int, default=125,
                        help='Specifies the sample rate, default 125.')
    parser.add_argument('-ms', dest='minspeech', type=float, default=0.1,
                        help='Specifies the minimum speech turn duration, \
                        default 0.1 seconds (roughly one word).')
    # This 0.3 second default comes from "The 2009 (RT-09) Rich
    # Transcription Meeting Recognition Evaluation Plan", page 4
    parser.add_argument('-mns', dest='minnonspeech', type=float, default=0.3,
                        help='Specifies the minimum nonspeech between-turns\
                        duration, default 0.3 seconds (NIST standard).')
    parser.add_argument('-sbe', dest='seg_before_exp', type=float, default=0.0,
                        help='Specifies a segment expansion time, that is, to\
                        remove some time before each detected speaker segment.\
                        No overlapping check, so set this to less than half \
                        the value of -mns. Default is 0.0 seconds (no expansion).')
    parser.add_argument('-see', dest='seg_end_exp', type=float, default=0.0,
                        help='Specifies a segment end expansion time, that is,\
                        to add some time after each detected speaker segment. \
                        No overlapping check, so set this to less than half \
                        the value of -mns. Default is 0.0 seconds (no expansion).')
    args = parser.parse_args()

    # Process arguments
    print 'Reading recipe from:', args.recfile
    with open(args.recfile, 'r') as recfile:
        recipe = parse_recipe(recfile)
    print 'Reading .exp files from:', args.exppath
    exppath = args.exppath
    if exppath[-1] != '/':
        exppath += '/'
    if not os.path.isdir(exppath):
        print 'Error,', exppath, 'is not a valid directory'
        exit()

    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'
    print 'Sample rate set to:', args.rate
    rate = float(args.rate)  # To ensure floating point division with it
    ms = args.minspeech
    print 'Minimum speech turn duration:', ms, 'seconds'
    mns = args.minnonspeech
    print 'Minimum nonspeech between-turns duration:', mns, 'seconds'
    sbe = args.seg_before_exp
    print 'Segment before expansion set to:', sbe, 'seconds'
    see = args.seg_end_exp
    print 'Segment end expansion set to:', see, 'seconds'

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            write_recipe(recipe, exppath, outf)
    else:
        write_recipe(recipe, exppath, outfile)
