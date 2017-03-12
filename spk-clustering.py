#!/usr/bin/env python2
import argparse
import sys
import re
import os.path as op
import numpy as np
from scipy.linalg import det
from scipy.linalg import pinv


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
            print 'Recipe line without recognizable data:'
            print line
    return r


def load_features(recipeLine, fpath, ext):
    """Load features from file"""
    ffile_name = fpath
    ffile_name += op.splitext(op.basename(recipeLine[0]))[0]
    ffile_name += ext
    #print 'Loading features from:', ffile_name
    with open(ffile_name, 'rb') as ffile:
        dim = int(np.fromfile(ffile, dtype=np.int32, count=1))
        features = np.fromfile(ffile, dtype=np.float32)
    #print 'Total features read:', features.size
    features = features.reshape((features.size / dim), dim)
    #print 'Final shape:', features.shape
    return dim, features


def get_spk_features(spk, features):
    arr = features[int(spk[0][0]):int(spk[0][1])]
    for s in spk[1:]:
        # TODO: This copies, should be much faster and less memory consuming
        # with views of the features, same everywhere else
        arr = np.concatenate((arr, features[int(s[0]):int(s[1])]))
    return arr


def write_recipe_line(recline, start, end, lna_start, speaker, outf, segf=None):
    """Write output recipes"""
    global lna_letter, lna_count
    lna = recline[1]
    if not args.dlr:
        if lna[:lna.find('_')] == lna_letter:
            lna_count += 1
        else:
            lna_count = 1
            lna_letter = lna[:lna.find('_')]
        lna = lna[:lna.find('_') + 1] + str(lna_count)
    outf.write('audio=' + recline[0] +
               ' lna=' + lna +
               ' start-time=' + str(start / rate + lna_start) +
               ' end-time=' + str(end / rate + lna_start) +
               ' speaker=speaker_' + str(speaker) + '\n')
    if segpath != '' and segf is not None:
        alignment = ' alignment=' + segpath + lna + '.seg'
        segf.write('audio=' + recline[0] +
                   alignment +
                   ' lna=' + lna +
                   ' start-time=' + str(start / rate + lna_start) +
                   ' end-time=' + str(end / rate + lna_start) +
                   ' speaker=speaker_' + str(speaker) + '\n')


def bic(arr1, arr2):
    """Bayes Information Criterion."""
    # Notes: In the seminal paper "Speakers, environment and channel
    # change detection and clustering via the Bayesian Information
    # Criterion" by Chen and Gopalakrishnan, they use a growing window
    # approach, so it's not directly comparable when using a fixed
    # sliding window.
    arr = np.concatenate((arr1, arr2))
    N1 = arr1.shape[0]
    N2 = arr2.shape[0]
    S1 = np.cov(arr1, rowvar=0)
    S2 = np.cov(arr2, rowvar=0)
    N = arr.shape[0]
    S = np.cov(arr, rowvar=0)
    d = 0.5 * N * np.log(det(S)) - 0.5 * N1 * np.log(det(S1))\
        - 0.5 * N2 * np.log(det(S2))
    p = arr.shape[1]
    corr = args.lambdac * 0.5 * (p + 0.5 * p * (p + 1)) * np.log(N)
    d -= corr
    return d


def glr(arr1, arr2):
    """Generalized Likelihood Ratio"""
    N1 = arr1.shape[0]
    N2 = arr2.shape[0]
    S1 = np.cov(arr1, rowvar=0)
    S2 = np.cov(arr2, rowvar=0)
    N = float(N1 + N2)
    # This is COV only version, not optimized (revise) but more robust
    # to environment noise conditions.
    # See Ulpu thesis pages 30-31, also Gish et al. "Segregation of
    # Speakers for Speech Recognition and Speaker Identification"
    d = -(N / 2.0) * ((N1 / N) * np.log(det(S1)) + (N2 / N) * np.log(det(S2))
                      - np.log(det((N1 / N) * S1 + (N2 / N) * S2)))
    # Ulpu version:
    # Includes the mean, theoretically less robust
    # arr = features[start:start+2*winsize]
    # S = cov(arr, rowvar=0)
    # d = -0.5*(N1*log(det(S1))+N2*log(det(S2))-N*log(det(S)))
    return d


def kl2(arr1, arr2):
    """Simmetric Kullback-Leibler distance"""
    S1 = np.cov(arr1, rowvar=0)
    S2 = np.cov(arr2, rowvar=0)
    m1 = np.mean(arr1, 0)
    m2 = np.mean(arr2, 0)
    delta = m1 - m2
    d = 0.5 * np.trace((S1 - S2) * (pinv(S2) - pinv(S1))) +\
        0.5 * np.trace((pinv(S1) + pinv(S2)) * delta * delta.T)
    return d


def spk_cluster_in(features, recline, speakers, outf, dist=bic, segf=None):
    """Clusters same speaker turns"""
    global total_segments
    global max_dist, min_dist, max_det_dist, min_det_dist
    start = int(recline[2] * rate)
    end = int(recline[3] * rate)
    arr2 = features[start:end]
    mind = sys.maxint
    spk = 0
    while spk < len(speakers):
        arr1 = get_spk_features(speakers[spk], features)
        # print start, end, speakers[spk], arr1.shape, arr2.shape
        d = dist(arr1, arr2)
        if args.tt:
            print 'Time:', end, '- Distance:', d, '- Speaker:', spk + 1
        # Ignore infinite distances (non-speech?) and record stats
        if d != np.inf and d != -np.inf:
            if d > max_dist:
                max_dist = d
            if d < min_dist:
                min_dist = d
            if d < mind:
                mind = d
                best_candidate = spk
        spk += 1
    if mind <= threshold:
        # Negative, same speaker!!
        # Stats should be of total detected speakers
        if d > max_det_dist:
            max_det_dist = d
        if d < min_det_dist:
            min_det_dist = d
        speakers[best_candidate].append((start, end))
        # best_candidate + 1 because we want speakers_ >= 1 in the output
        write_recipe_line(recline, start, end, 0, best_candidate + 1,
                          outf, segf)
    else:  # Positive, new speaker!
        speakers.append([(start, end)])
        write_recipe_line(recline, start, end, 0, len(speakers),
                          outf, segf)


def spk_cluster_hi(features, recipe, speakers, outf, dist=bic, segf=None):
    """Clusters same speaker turns"""
    global total_segments
    global max_dist, min_dist, max_det_dist, min_det_dist
    sp = len(speakers)
    # distances = np.empty((sp, sp), dtype=int)
    distances = np.empty((sp, sp))
    np.fill_diagonal(distances, sys.maxint)
    mind = sys.maxint
    # Get all initial distances
    for s1 in xrange(sp):
        for s2 in xrange(s1 + 1, sp):
            arr1 = get_spk_features(speakers[s1], features)
            arr2 = get_spk_features(speakers[s2], features)
            d = dist(arr1, arr2)
            distances[s1][s2] = d
            distances[s2][s1] = d
            # Ignore infinite distances (non-speech?) and record stats
            if d != np.inf and d != -np.inf:
                if d > max_dist:
                    max_dist = d
                if d < min_dist:
                    min_dist = d
    while True:
        # Get min d
        mind = distances.min()
        index = distances.argmin()
        best_candidates = (index / len(speakers), index % len(speakers))
        best_candidates = (min(best_candidates), max(best_candidates))
        if mind <= threshold or (args.max_spk > 0
                                 and len(speakers) > args.max_spk):
            # Negative, fuse speakers!!
            if mind > max_det_dist:
                max_det_dist = mind
            if mind < min_det_dist:
                min_det_dist = mind
            print 'Merging:', best_candidates[0] + 1, 'and',\
                  best_candidates[1] + 1, 'distance:', mind
            speakers[best_candidates[0]].extend(speakers[best_candidates[1]])
            speakers.pop(best_candidates[1])
            # Recalculating new speaker distances vs rest
            s1 = best_candidates[0]
            s1b = best_candidates[1]
            # s1b is "out"
            distances = np.delete(distances, s1b, 0)
            distances = np.delete(distances, s1b, 1)
            for s2 in xrange(len(speakers)):
                if s2 == s1:
                    continue
                arr1 = get_spk_features(speakers[s1], features)
                arr2 = get_spk_features(speakers[s2], features)
                d = dist(arr1, arr2)
                distances[s1][s2] = d
                distances[s2][s1] = d
                # Ignore infinite distances (non-speech?) and record stats
                if d != np.inf and d != -np.inf:
                    if d > max_dist:
                        max_dist = d
                    if d < min_dist:
                        min_dist = d
        else:
            # Convergence
            break
    # All done, time to write the output recipe
    print 'Final speakers:', len(speakers)
    while True:
        # TODO: Sloooowww
        candidate = None
        for s in xrange(len(speakers)):
            if candidate is None and speakers[s] != []:
                candidate = (s, min(speakers[s]))
            elif speakers[s] != []:
                candidate2 = min(speakers[s])
                if candidate2 < candidate[1]:
                    candidate = (s, candidate2)
        if candidate is None:
            # No more to write
            break
        else:
            speakers[candidate[0]].remove(candidate[1])
            write_recipe_line(recipe[candidate[1][2]], candidate[1][0],
                              candidate[1][1], 0, candidate[0] + 1, outf,
                              segf)


def process_recipe(recipe, speakers, outf, segf=None):
    """Process recipe, outputs a new recipe"""
    this_wav = ''
    l = 0
    while l < len(recipe):
        if recipe[l][0] != this_wav:
            this_wav = recipe[l][0]
            feas = load_features(recipe[l], feapath, feaext)
            # Should I empty detected speakers here for a new wav?  Maybe not,
            # if batch processing in the same recipe the wavs should be
            # related
        if speakers == [] and args.method == 'in':
            speakers.append([(recipe[l][2] * rate, recipe[l][3] * rate)])
            write_recipe_line(recipe[l], recipe[l][2] * rate,
                              recipe[l][3] * rate, 0, len(speakers),
                              outf, segf)
        elif args.method == 'hi':
            # Populate for initial clustering
            speakers.append([(recipe[l][2] * rate, recipe[l][3] * rate, l)])
        else:
            # args.method == 'in', after first speaker initialization
            spk_cluster_m(feas[1], recipe[l], speakers, outf,
                          dist, segf)
        l += 1
    if args.method == 'hi':
        # Initial clustering done, ready to start
        # TODO: Multiple wavs on same recipe fails
        print 'Initial cluster with:', len(speakers), 'speakers'
        spk_cluster_m(feas[1], recipe, speakers, outf,
                      dist, segf)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Perform speaker clustering,\
             using a distance measure.')
    parser.add_argument('recfile', type=str,
                        help='Specifies the input recipe file')
    parser.add_argument('feapath', type=str,
                        help='Specifies the features files path')
    parser.add_argument('-seg', dest='segpath', type=str, default='',
                        help='Specifies the alignment segmentation files path\
                        and generates "alignment=" information, default empty\
                        (not generate)')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout,
                        help='Specifies an output file, default stdout. If\
                        specified with the "-seg" option, a second output file\
                        will be created with "-seg" appended to the name\
                        before the extension')
    parser.add_argument('-fe', dest='feaext', type=str, default='.fea',
                        help='Specifies feature file extension, default ".fea"')
    parser.add_argument('-se', dest='segext', type=str, default='.seg',
                        help='Specifies segmentation files extension, default ".seg"')
    parser.add_argument('-f', dest='frame_rate', type=int, default=125,
                        help='Specifies the frame rate, default 125')
    parser.add_argument('-m', dest='method', type=str,
                        choices=['in', 'hi'], default='hi',
                        help='Specifies the clustering method, hierarchical\
                        agglomerative or in-order consecutive clustering.\
                        Default hierarchical (slower but more accurate).')
    parser.add_argument('-d', dest='distance', type=str,
                        choices=['GLR', 'BIC', 'KL2'], default='BIC',
                        help='Sets the distance measure to use, defaults to\
                        Bayesian Information Criterion (BIC). Generalized\
                        Likelihood Ration (GLR) or symmetric Kullback-Leibler\
                        (KL2) are other possibilities.')
    parser.add_argument('-t', dest='threshold', type=float, default=0.0,
                        help='Specifies threshold distance for detection,\
                        default 0.0 (nonsensical handpicked, tune it except\
                        for BIC).')
    parser.add_argument('-ms', dest='max_spk', type=int, default=0,
                        help='Specifies the maximum speakers stopping criteria\
                        for hierarchical clustering, default 0 (use only the\
                        threshold as stopping criteria')
    parser.add_argument('-l', dest='lambdac', type=float, default=1.3,
                        help='Lambda penalty weight for BIC, default 1.3')
    parser.add_argument('-tt', action='store_true',
                        help='If set, outputs all the decision thresholds in\
                        every clustering attempt, useful to define a proper\
                        threshold.')
    parser.add_argument('-dlr', action='store_true',
                        help='If set, disables lna renaming, so it keeps the lna\
                        original names (if there are two speakers in the same\
                        lna, start and end line should be used for adaptation).\
                        By default it renames so that all segments have a\
                        a different rna name.')
    args = parser.parse_args()

    # Process arguments
    print 'Reading recipe from:', args.recfile
    with open(args.recfile, 'r') as recfile:
        parsed_recipe = parse_recipe(recfile)

    print 'Reading feature files from:', args.feapath
    feapath = args.feapath
    if feapath[-1] != '/':
        feapath += '/'

    if args.segpath != '':
        print 'Setting alignment segmentation files path to:', args.segpath
        if args.segpath[-1] != '/':
            args.segpath += '/'
        print 'Segmentation files extension:', args.segext
    segpath = args.segpath
    segext = args.segext

    print 'Feature files extension:', args.feaext
    feaext = args.feaext

    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
        if segpath != '':
            segfile = op.splitext(outfile)[0]
            segfile += '-seg' + op.splitext(outfile)[1]
            print 'Writing seg output to:', segfile
        else:
            segfile = False
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    rate = float(args.frame_rate)
    print 'Conversion rate set to frame rate:', rate

    if args.method == 'hi':
        print 'Using hierarchical clustering'
        spk_cluster_m = spk_cluster_hi
    elif args.method == 'in':
        print 'Using in-order consecutive clustering'
        spk_cluster_m = spk_cluster_in

    if args.distance == 'GLR':
        print 'Using GLR as distance measure'
        dist = glr
    elif args.distance == 'BIC':
        print 'Using BIC as distance measure, lambda =', args.lambdac
        dist = bic
    elif args.distance == 'KL2':
        print 'Using KL2 as distance measure'
        dist = kl2

    print 'Threshold distance:', args.threshold
    threshold = args.threshold
    print 'Maximum speakers:', args.max_spk

    lna_letter = 'a'
    lna_count = 0
    if args.dlr:
        print 'Disabling LNA renaming'

    # End of argument processing

    # Some useful metrics
    max_dist = 0
    min_dist = sys.maxint
    max_det_dist = 0
    min_det_dist = sys.maxint

    # Detected speakers
    speakers = []

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            if segfile:
                with open(segfile, 'w') as segf:
                    process_recipe(parsed_recipe, speakers, outf, segf)
            else:
                process_recipe(parsed_recipe, speakers, outf)

    else:
        process_recipe(parsed_recipe, speakers, outfile)

    print 'Useful metrics for determining the right threshold:'
    print '---------------------------------------------------'
    print 'Maximum between segments distance:', max_dist
    if min_dist < sys.maxint:
        print 'Minimum between segments distance:', min_dist
    print 'Total segments:', len(parsed_recipe)
    print 'Total detected speakers:', len(speakers)
