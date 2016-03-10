#!/usr/bin/python2
import argparse
import sys
import os
import os.path as op
import tempfile
from subprocess import Popen, call
from mimetypes import guess_type


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a media file to perform\
                                     segmentation and speaker clustering on it.')
    parser.add_argument('infile', type=str,
                        help='Specifies the media file')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout,
                        help='Specifies an output recipe file, default stdout.')
    # parser.add_argument('-of', dest='outformat', type=str,
    #                     choices=['aku', 'elan', 'ann'], default='aku',
    #                     help='Specifies an output format, defaults to aku recipe\
    #                     file, but includes support for ELAN .eaf and simple\
    #                     annotation files.')
    parser.add_argument('-cs', dest='cspath', type=str, default=os.getcwd() + '/VAD/tokenpass',
                        help='Specifies the path to classify_speecon.pl')
    parser.add_argument('-fc', dest='fcpath', type=str, default=os.getcwd(),
                        help='Specifies the path to feacat, defaults to ./')
    parser.add_argument('-fcfg', dest='fcfg', type=str, default=os.getcwd() + '/fconfig.cfg',
                        help='Specifies the feacat acoustic model config, defaults ./fconfig.cfg')
    parser.add_argument('-lna', dest='lnapath', type=str, default=os.getcwd() + '/tmp/lna',
                        help='Specifies the path to the exp files, defaults to ./tmp/lna')
    parser.add_argument('-exp', dest='exppath', type=str, default=os.getcwd() + '/tmp/exp',
                        help='Specifies the path to the exp files, defaults to ./tmp/exp')
    parser.add_argument('-fp', dest='feapath', type=str, default=os.getcwd() + '/tmp/fea',
                        help='Specifies the path to the feature files, defaults to ./tmp/fea')
    parser.add_argument('-tmp', dest='tmppath', type=str, default=os.getcwd() + '/tmp/',
                        help='Specifies where to write the temporal files, defaults to ./tmp')
    args = parser.parse_args()

    # Process arguments
    if not op.isfile(args.infile):
        print '%s does not exist, exiting' % args.infile
        sys.exit()
    print 'Reading file:', args.infile

    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    if args.cspath[-1] != '/':
        args.cspath += '/'
    cspeecon = args.cspath + 'classify_speecon.pl'
    if not op.isfile(cspeecon):
        print '%s does not exist, exiting' % cspeecon
        sys.exit()
    print 'Using classify speecon from:', args.cspath

    if args.fcpath[-1] != '/':
        args.fcpath += '/'
    args.fcpath += 'feacat'
    if not op.isfile(args.fcpath):
        print '%s does not exist, exiting' % args.feacat
        sys.exit()
    print 'Using feacat from:', args.fcpath

    if args.tmppath[-1] != '/':
        args.tmppath += '/'
        if not op.exists(args.tmppath):
            print 'Path %s for temporal files does not exist, please make sure\
            it\'s a correct path or create the folder, exiting' % args.tmppath
            sys.exit()
    print 'Writing temporal files in:', args.tmppath

    if args.lnapath[-1] != '/':
        args.lnapath += '/'
        if not op.exists(args.lnapath):
            print 'Path %s does not exist, exiting' % args.lnapath
            sys.exit()
    print 'Writing lna files in:', args.lnapath

    if args.exppath[-1] != '/':
        args.exppath += '/'
        if not op.exists(args.exppath):
            print 'Path %s does not exist, exiting' % args.exppath
            sys.exit()
    print 'Writing exp files in:', args.exppath

    if args.feapath[-1] != '/':
        args.feapath += '/'
        if not op.exists(args.exppath):
            print 'Path %s does not exist, exiting' % args.feapath
            sys.exit()
    print 'Writing features in:', args.feapath
    # End of argument processing

    # Checking if media file is .wav audio
    mediatype = guess_type(args.infile)[0]
    if mediatype != 'audio/x-wav':
        print 'Media is not a .wav audio file, attempting to extract a .wav file'
        print 'Calling ffmpeg'
        infile = os.path.splitext(args.infile)[0] + '.wav'
        call(['ffmpeg', '-i', args.infile, '-ar', '16000', '-ac', '1',
             '-ab', '32k', infile])
    else:
        infile = args.infile

    # Prepare an initial temporal recipe
    init_recipe = tempfile.mkstemp(suffix='.recipe', prefix='init', dir=args.tmppath)[1]
    init_file = open(init_recipe, 'w')
    init_file.write('audio=' + infile + '\n')
    init_file.close()

    print 'Calling classify_speecon.pl and feacat concurrently'
    cs_env = os.environ.copy()
    cs_env['PERLLIB'] = args.cspath + ':' + cs_env.get('PERLLIB', '')
    child1 = Popen([cspeecon, init_recipe, args.lnapath, args.exppath],
                   env=cs_env, cwd=args.cspath)

    # TODO: Uncomment this and remove the sys.exit() below when we have the
    # acoustic models
    # feafile = open(op.splitext(args.feapath + op.basename(infile))[0] + '.fea', 'w')
    # child2 = Popen([args.fcpath, '-c', args.fcfg, '-H', '--raw-output',
    #                 infile], stdout=feafile)

    # We need the exp files ready here
    child1.wait()
    sys.exit()
    print 'Calling voice-detection.py'
    vad_recipe = tempfile.mkstemp(suffix='.recipe', prefix='vad',
                                  dir=args.tmppath)[1]
    call(['./voice-detection.py', init_recipe, args.exppath,
          '-o', vad_recipe, '-ms', '0.1', '-mns', '1.5', '-see', '0.3'])

    # We need to wait for the features to be ready here
    print 'Waiting for feacat to end.'
    child2.wait()

    spkchange_recipe = tempfile.mkstemp(suffix='.recipe', prefix='spkc',
                                        dir=args.tmppath)[1]
    print 'Calling spk-change-detection.py'
    call(['./spk-change-detection.py', vad_recipe, args.feapath,
          '-o', spkchange_recipe, '-m', 'gw', '-d', 'BIC', '-w', '3.0',
          '-st', '3.0', '-l', '1.0'])

    print 'Calling spk-clustering.py'
    call(['./spk-clustering.py', spkchange_recipe, args.feapath,
          '-o', outfile, '-m', 'hi', '-l', '1.3'])

    # Outputting alternative formats
    outf = os.path.splitext(os.path.basename(outfile))[0]
    print 'Calling aku2ann.py'
    call(['./aku2ann.py', outfile,
         '-o', outf + '.ann'])

    print 'Calling aku2elan.py'
    call(['./aku2elan.py', outfile,
         '-o', outf + '.eaf'])
