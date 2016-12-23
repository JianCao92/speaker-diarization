#!/usr/bin/env python2
"""Generate exp files.

Creates .exp files for use with `voice_detection.py`.

Given a recipe with audio files to process, they are processed for
speech/non-speech probabilities against a model.

Requires `phone_probs` from AaltoASR aku package.

Models are:
- mfcc_16g_9.10.2007_10  # public place noise
- mfcc_16g_11.10.2007_10 # more public place noise
- mfcc_16g_15.10.2007_10 # even more public place noise

Usage:
    generate_exp.py [-l PATH] [-e PATH] [-m MODEL] [-a PATH] [-t PATH] RECIPE

    Arguments:
        RECIPE                    Recipe with audio files to process.

    Options:
        -h, --help                 Show this screen.
        --version                  Show version.
        -l PATH, --lnapath PATH    Choose a folder to drop the lna files [default: ./lna]
        -e PATH, --exppath PATH    Choose a folder to drop the exp files [default: ./exp]
        -m MODEL, --model MODEL    Choose a model [default: ./hmms/mfcc_16g_11.10.2007_10]
        -a PATH, --asrpath PATH    Path to AaltoASR package [default: ./AaltoASR]
        -t PATH, --tokenpass PATH  Path to binary `test_token_pass` [default: ./VAD/tokenpass/test_token_pass]
"""
import sys
import os
import os.path as op
import re
from subprocess import call
import numpy as np
from docopt import docopt
from tempfile import mkstemp


def validate_arguments(arguments):
    """Validate commandline arguments."""
    if not op.exists(arguments['RECIPE']):
        print 'ERROR:', arguments['RECIPE'], 'does not exist.'
        exit()
    if not op.isdir(arguments['--lnapath']):
        _create_argpath(arguments['--lnapath'])
    if not op.isdir(arguments['--exppath']):
        _create_argpath(arguments['--exppath'])
    # Check for the .cfg file of the model
    if not op.isfile(arguments['--model'] + '.cfg'):
        print 'ERROR:', arguments['--model'], 'does not exist.'
        exit()
    # Check for `phone_probs`
    arguments['PPROBS'] = op.join(arguments['--asrpath'], 'build', 'aku',
                                  'phone_probs')
    if not op.isfile(arguments['PPROBS']):
        print 'ERROR: Unable to find `phone_probs` in', arguments['PPROBS']
        exit()
    dec_path = op.join(arguments['--asrpath'], 'build', 'decoder', 'src', 'swig')
    try:
        sys.path.append(dec_path)
        global Decoder
        import Decoder
    except ImportError:
        print 'ERROR: Decoder.py not found in', arguments['DEC']
        exit()
    print 'tokenpass:', arguments['--tokenpass']
    if not op.isfile(arguments['--tokenpass']):
        print 'ERROR: Unable to find `test_token_pass` in',
        arguments['--tokenpass']
        exit()

    print 'Reading recipe:', arguments['RECIPE']
    print 'Using model:', arguments['--model']
    print 'Writing `.lna` files in:', arguments['--lnapath']
    print 'Writing `.exp` files in:', arguments['--exppath']


def _create_argpath(argpath):
    """Create a folder in argpath."""
    print 'ERROR:', argpath, 'is not a valid directory.'
    create = raw_input('Attempt to create? [y/N]: ') or 'N'
    if create == 'y' or create == 'Y':
        try:
            os.mkdir(argpath)
        except Exception as e:
            print 'Unable to create path:', e
            exit()
    else:
        print 'Unable to continue without valid', argpath
        exit()


def generate_lnas(arguments):
    """Generate state (speech or non-speech) probabilites -> lna-files."""
    cmd = "{PPROBS} -b {--model} -c {--model}.cfg -r {RECIPE} -a -o {--lnapath} -i 1 --lnabytes=4".format(**arguments)
    call(cmd.split())


def get_lnas(arguments):
    """Get list of generated lnas."""
    path = arguments['--lnapath']
    audio_file = re.compile('audio=(\S+)')
    lnas = []
    with open(arguments['RECIPE']) as rec:
        for line in rec:
            if line != '\n':
                wavname = op.splitext(op.basename(audio_file.search(line).groups()[0]))[0]
                lnas.append(op.join(path, wavname + '.lna'))
    return lnas


def _lna2exp(exppath, lna):
    """Get .exp related file of a .lna"""
    name = op.splitext(op.basename(lna))[0]
    return op.join(exppath, name + '.exp')



def _read_lna(lna):
    """Read an lna file."""
    with open(lna, 'r') as f:
        num_models = np.fromfile(f, np.uint8, count=4)
        dim = np.sum(num_models * np.array([16777216, 4096, 256, 1]))
        num_bytes = np.fromfile(f, np.int8, count=1)[0]
        if num_bytes == 4:
            dtype = np.float32
        else:
            dtype = np.int16
        return num_models, np.fromfile(f, dtype).reshape((dim, -1)).astype(np.float64)


def _write_lna(lna, num_models, data, exppath):
    """Write an lna file."""
    with open(lna, 'w') as f:
        num_models.tofile(f)
        np.array([4], dtype=np.int8).tofile(f)
        data.astype(np.float32).tofile(f)
    # Saving last frame in a separate file, needed for tokenpass.pm
    last_frame = "%d" % data.shape[1]
    lf_file = op.join(exppath, op.splitext(op.basename(lna))[0] + '.last_frame')
    with open(lf_file, 'w') as f:
        f.write(last_frame)


def _clean_decoder_output(buf):
    """Clean the decoder output."""
    valid_line = re.compile(r'(p|<w>) run\(\) in frame (\d+)')
    return ' '.join([l.group(2) + ' ' + l.group(1) for l in valid_line.finditer(buf)])


class redirect_stdout(object):
    """
    A context manager for doing a "deep redirection" of stdout in Python, i.e.
    will redirect all prints to a file descriptor, even if the print originates
    in a compiled C/Fortran sub-function.

    Original Source:
    http://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions
    """
    def __init__(self, fd):
        # Open a pair of null files
        # Save the real stdout (1) file descriptors.
        self.fd = fd
        self.real_stdout = os.dup(1)

    def __enter__(self):
        # Assign the buffer to stdout.
        os.dup2(self.fd, 1)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.real_stdout, 1)


def shift_dec_bord(lnas, exppath):
    """Shift decision border for lna files."""
    shift_bord = 0.2
    for lna in lnas:
        num_models, l = _read_lna(lna)
        l = np.exp(l)
        l[1, :] *= shift_bord
        l /= sum(l)
        l = np.log(l)
        _write_lna(lna, num_models, l, exppath)



def classify(lnas, model, exppath):
    """Label lna states as speech/non-speech, outputs in .exp files.

    Basically replaces the old `test_token_pass` binary.
    """
    hmms = model + '.ph'
    lexicon = './models/sp_nsp.lex'
    ngram = './models/malli.bin'
    t = Decoder.Toolbox(0, hmms, None)  # 0 tokenpass, 1 stack decoder
    # Some parameters have been disassembled from the compiled binary
    # `test_token_pass` that was in the old Voice Activity Detection software.
    t.set_lm_lookahead(0)
    t.set_require_sentence_end(False)  # True in `test_token_pass`
    t.set_optional_short_silence(True)
    t.set_cross_word_triphones(False)
    global_beam = 120.0
    t.set_global_beam(int(global_beam))  # 320 in `test_token_pass`
    t.set_word_end_beam(int(2*global_beam/3))  # 200 in `test_token_pass`
    # t.set_word_end_beam(100)  # 200 in `test_token_pass`
    t.set_token_limit(30000)
    t.set_prune_similar(2)
    t.set_word_boundary('<w>')
    t.set_print_text_result(True)
    t.set_print_state_segmentation(False)
    t.set_print_frames(True)  # Only works in stack decoder
    t.set_print_probs(False)
    t.set_print_indices(False)
    # These 3 from tokenpass.pm
    t.set_transition_scale(2)  # 1 in `test_token_pass`
    t.set_lm_scale(10)  # 10 in `test_token_pass`
    t.set_insertion_penalty(1)  # 1 in `test_token_pass`
    # Put > 1 to print run frame, > 0 to print text_result
    t.set_verbose(2)
    t.set_duration_scale(3)
    # Load our models
    t.lex_read(lexicon)
    # t.set_sentence_boundary("<s>", "</s>")  # Fails
    t.ngram_read(ngram, True)
    # t.run() prints to stdout, redirecting to a temporary file
    for lna in lnas:
        stdout_buffer = mkstemp()[1]
        with open(stdout_buffer, 'w') as f:
            with redirect_stdout(f.fileno()):
                t.lna_open(lna, 1024)
                t.reset(0)
                t.set_end(-1)
                while t.run(): pass

        with open(stdout_buffer, 'r') as f:
            stdo_buffer = f.read()
        with open(_lna2exp(exppath, lna), 'w') as f:
            f.write(_clean_decoder_output(stdo_buffer))
            # f.write(stdo_buffer)


def classify_old(tokenpass, lnas, model, exppath):
    """Call the old binary `test_token_pass`, no code available.

    Eventully we will remove this, but for now `classify` doesn't have the same
    performance as this one.
    """
    args_dict = {'tokenpass': tokenpass,
                 'model': model + '.ph'}
    for lna in lnas:
        print 'Generating exp for lna file:', lna
        args_dict['lna'] = lna
        cmd = "{tokenpass} -model {model} -ins_pen 1 -lm_scale 10 -trans_scale 1 -lna {lna}".format(**args_dict)
        with open(_lna2exp(exppath, lna), 'w') as f:
            call(cmd.split(), stdout=f)


if __name__ == '__main__':
    arguments = docopt(__doc__, version='1.0')
    validate_arguments(arguments)
    generate_lnas(arguments)
    lnas = get_lnas(arguments)
    shift_dec_bord(lnas, arguments['--exppath'])
    # classify(lnas, arguments['--model'], arguments['--exppath'])
    classify_old(arguments['--tokenpass'], lnas, arguments['--model'], arguments['--exppath'])
