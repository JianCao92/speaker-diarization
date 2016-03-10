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
    ffile_name = op.splitext(op.basename(recipeLine[0]))[0]
    ffile_name += ext
    ffile_name = op.join(fpath, ffile_name)
    #print 'Loading features from:', ffile_name
    with open(ffile_name, 'rb') as ffile:
        dim = int(np.fromfile(ffile, dtype=np.int32, count=1))
        features = np.fromfile(ffile, dtype=np.float32)
    #print 'Total features read:', features.size
    features = features.reshape((features.size / dim), dim)
    #print 'Final shape:', features.shape
    return dim, features


def write_recipe_line(recline, start, end, lna_start, outf, segf=None):
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
               ' speaker=spk_turn\n')
    if segpath and segf is not None:
        alignment = ' alignment=' + segpath + lna + '.seg'
        segf.write('audio=' + recline[0] +
                   alignment +
                   ' lna=' + lna +
                   ' start-time=' + str(start / rate + lna_start) +
                   ' end-time=' + str(end / rate + lna_start) +
                   ' speaker=spk_turn\n')


def bic(arr1, arr2, arr, i=0, saved={}):
    """Bayes Information Criterion

    Notes: In the seminal paper "Speakers, environment and channel change
    detection and clustering via the Bayesian Information Criterion" by Chen
    and Gopalakrishnan, they use a growing window approach, so it's not
    directly comparable when using a fixed sliding window.

    In BIC, we can save the first matrix calculations since in growing windows
    these keep repeating all the time, and we are saving just one float so
    it's also memory efficient and saves a lot of time (Antonio)"""

    if i in saved:
        c1 = saved[i]
    else:
        S1 = np.cov(arr1, rowvar=0)
        N1 = arr1.shape[0]
        c1 = 0.5 * N1 * np.log(det(S1))
        saved[i] = c1
    S2 = np.cov(arr2, rowvar=0)
    N2 = arr2.shape[0]
    N = arr.shape[0]
    S = np.cov(arr, rowvar=0)
    d = 0.5 * N * np.log(det(S)) - c1\
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
    N = float(N1 + N2)  # To force float divisions with it
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


def merge_rec(features, recline1, recline2, outf, dist=bic, segf=None):
    """Merges consecutive turns with the same speaker"""
    global total_dist, total_windows, total_det_dist, total_segments
    global max_dist, min_dist, max_det_dist, min_det_dist
    start1 = merge_rec.prev[2] * rate
    start2 = recline2[2] * rate
    end1 = merge_rec.prev[3] * rate
    end2 = recline2[3] * rate
    arr1 = features[start1:end1]
    arr2 = features[start2:end2]
    #print start1, end1, start2, end2, features.shape, arr1.shape, arr2.shape
    if dist == bic:
        arr = np.concatenate((arr1, arr2))
        d = dist(arr1, arr2, arr)
    else:
        d = dist(arr1, arr2)
    if args.tt:
        print 'Time:', end1, '- Distance:', d
    # Ignore infinite distances (non-speech?) and record stats
    if d != np.inf and d != -np.inf:
        total_dist += d
        total_windows += 1
        if d > max_dist:
            max_dist = d
        if d < min_dist:
            min_dist = d
    if d < threshold and d != np.inf and d != -np.inf:  # Negative, merge
        #print 'Merging:', start1, end1, start2, end2
        merge_rec.prev = (merge_rec.prev[0], merge_rec.prev[1],
                          merge_rec.prev[2], recline2[3])
        # Stats should be of total merged segments
        total_det_dist += d
        total_segments += 1
        if d > max_det_dist:
            max_det_dist = d
        if d < min_det_dist:
            min_det_dist = d
    else:  # Positive, write previous one if not written
        #print 'Positive:', start1, end1, start2, end2
        write_recipe_line(merge_rec.prev, merge_rec.prev[2] * rate,
                          merge_rec.prev[3] * rate, 0, outf, segf)
        merge_rec.prev = (recline2[0], recline2[1], recline2[2], recline2[3])


def dist_gw(features, recline, outf, dist=bic, segf=None):
    """Detects speaker turn changes with a growing window approach. Some
    optimizations (marked with *) from the paper "Improved speaker
    segmentationand segments clustering using the Bayes Information
    Criterion", Alain Tritschler and Ramesh Gopinath, are implemented too,
    together with some of my own ideas (istep + 2nd pass fine tune,
    Antonio)."""
    global total_dist, total_windows, total_det_dist, total_segments
    global max_dist, min_dist, max_det_dist, min_det_dist
    lna_start = recline[2]
    lna_end = recline[3]
    start = 0
    end = start + winsize * 2
    # Minimum features to consider, about half a second
    minfeas = rate / 2
    # Step size of about 0.1 seconds instead of frame by frame (A)
    istep = rate / 10
    # (*) Initial winstep and delta ws
    ws = minfeas
    dws = deltaws
    saved_calculations = {}
    while end <= features.shape[0]:
        i = minfeas
        maxd = -sys.maxint - 1
        while i < end - start - minfeas:
            arr1 = features[start:start + i]
            arr2 = features[start + i:end]
            if dist == bic:
                arr = features[start:end]
                d = dist(arr1, arr2, arr, i, saved_calculations)
            else:
                d = dist(arr1, arr2)
            if args.tt:
                print 'Time:', start / rate + i / rate +\
                      lna_start, '- Distance:', d
            if d > maxd and d != np.inf:
                maxd = d
                maxi = i
                #print arr.shape, arr1.shape, arr2.shape, maxd
            elif d == np.inf or d == -np.inf:
                print 'Inf:', arr1.shape, arr2.shape, d
            i += istep  # (A)
        # Ignore infinite distances (non-speech?) and record stats
        if maxd != np.inf and maxd != -np.inf:
            total_dist += maxd
            total_windows += 1
            if maxd > max_dist:
                max_dist = maxd
            if maxd < min_dist:
                min_dist = maxd
        if maxd > threshold and maxd != np.inf and maxd != -np.inf:
            # Positive, fine-tune best frame (A)
            # TODO: We should fine-tune even if not positive to avoid
            # skipping a changing point
            # print start + maxi, start, end, arr1.shape, arr2.shape
            i = maxi - istep
            endtune = maxi + istep
            while i < endtune:
                arr1 = features[start:start + i]
                arr2 = features[start + i:end]
                if dist == bic:
                    arr = features[start:end]
                    d = dist(arr1, arr2, arr, i, saved_calculations)
                else:
                    d = dist(arr1, arr2)
                if d > maxd and d != np.inf:
                    maxd = d
                    maxi = i
                    #print arr.shape, arr1.shape, arr2.shape, maxd
                elif d == np.inf or d == -np.inf:
                    print 'Inf:', arr1.shape, arr2.shape, d
                i += 1
            # Write it down
            # print 'Distance of this decision:', maxd
            write_recipe_line(recline, start, start + maxi, lna_start, outf, segf)
            # Reset the saved calculations
            saved_calculations = {}
            total_det_dist += maxd
            total_segments += 1
            if maxd > max_det_dist:
                max_det_dist = maxd
            if maxd < min_det_dist:
                min_det_dist = maxd
            start += maxi
            if start + winsize * 2 <= features.shape[0]:
                end = start + winsize * 2
                # (*) Reset initial winstep and delta ws
                ws = minfeas
                dws = deltaws
            else:  # Not enough for another decision, just write the last part
                break
        else:  # Negative
            #print 'Enlarging the window'
            if end + ws <= features.shape[0]:
                end += ws
                # (*) Enlarging winstep and delta ws for next time
                if ws < winstep:
                    ws += dws
                    dws *= 2
                if ws > winstep:
                    ws = winstep
            elif end != features.shape[0]:
                end = features.shape[0]
            else:  # Not enough for another decision, just write the last part
                break
    # Write the last turn (recline end):
    #print 'Last line:', start, features.shape[0], lna_start
    end = (lna_end - lna_start) * rate
    write_recipe_line(recline, start, end, lna_start, outf, segf)


def dist_sw(features, recline, outf, dist=glr, segf=None):
    """Distance function, detects speaker turn changes"""
    global total_dist, total_windows, total_det_dist, total_segments
    global max_dist, min_dist, max_det_dist, min_det_dist
    #arr1 = empty((winsize, features.shape[1]))
    #arr2 = empty((winsize, features.shape[1]))
    lna_start = recline[2]
    lna_end = recline[3]
    start = 0
    end = 0
    bestd = -1
    best_position = -1
    last_positive = -1
    while start + 2 * winsize <= features.shape[0]:
        arr1 = features[start:start + winsize]
        arr2 = features[start + winsize:start + 2 * winsize]
        #print arr1.shape, arr2.shape
        if dist == bic:
            arr = features[start:end]
            d = dist(arr1, arr2, arr)
        else:
            d = dist(arr1, arr2)
        if args.tt:
            print 'Time:', (start + winsize) / rate + lna_start,\
                  '- Distance:', d
        # Ignore infinite distances (non-speech?) and record stats
        if d != np.inf and d != -np.inf:
            total_dist += d
            total_windows += 1
            if d > max_dist:
                max_dist = d
            if d < min_dist:
                min_dist = d
        if d < threshold or d == np.inf or d == -np.inf:
        # Negative... end of a consecutive positive series?
            if start - winstep == last_positive:
                write_recipe_line(recline, end, best_position, lna_start, outf, segf)
                total_det_dist += bestd
                total_segments += 1
                if bestd > max_det_dist:
                    max_det_dist = bestd
                if bestd < min_det_dist:
                    min_det_dist = bestd
                bestd = 0
                end = best_position
        else:  # Positive, possibly in a consecutive series
            if d > bestd:
                bestd = d
                best_position = start + winsize
            last_positive = start
        start += winstep
    # Recipe ending in positive change... write the most probable one of the
    # last consecutive positive series (NOTE: Threshold might be too high if
    # this is necessary
    if start - winstep == last_positive:
        write_recipe_line(recline, end, best_position, lna_start, outf, segf)
        total_det_dist += bestd
        total_segments += 1
        if bestd > max_det_dist:
            max_det_dist = bestd
        if bestd < min_det_dist:
            min_det_dist = bestd
        bestd = 0
        end = best_position
    # Write the last turn (recline end):
    this_end = (lna_end - lna_start) * rate
    write_recipe_line(recline, end, this_end, lna_start, outf, segf)


def detect_changes(recipe, outf, segf=None):
    """Detect speaker changes, outputs a new recipe"""
    this_wav = ''
    this_lna = ''
    l = 0
    wav_start = True
    while l < len(recipe):
        if recipe[l][0] != this_wav:
            this_wav = recipe[l][0]
            feas = load_features(recipe[l], feapath, feaext)
        if dfun != merge_rec:
            if recipe[l][1] != this_lna:
                this_lna = recipe[l][1]
                dfun(feas[1][recipe[l][2] * rate:recipe[l][3] * rate],
                     recipe[l], outf, dist, segf)
        else:  # Merge mode
            if l + 1 < len(recipe):
                if recipe[l + 1][0] != this_wav:
                    # Can't merge these ones
                    l += 1
                    wav_start = True
                    continue
                # Should return last start-end so in the next round we try
                # against those, in case a merger were done (so we don't try
                # with recipe[l] ones)
                if wav_start:  # First one
                    wav_start = False
                    merge_rec.prev = recipe[l]
                merge_rec(feas[1],
                          recipe[l], recipe[l + 1], outf,
                          dist, segf)
            else:  # Last segment, write as it is
                write_recipe_line(merge_rec.prev,
                                  merge_rec.prev[2] * rate,
                                  merge_rec.prev[3] * rate, 0, outf, segf)
        l += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Perform speaker turn \
            segmentation, using a distance measure.')
    parser.add_argument('recfile', type=str,
                        help='Specifies the input recipe file')
    parser.add_argument('feapath', type=str,
                        help='Specifies the features files path')
    parser.add_argument('-seg', dest='segpath', type=str, default=None,
                        help='Specifies the alignment segmentation files path\
                        and generates "alignment=" information, default empty\
                        (not generate)')
    parser.add_argument('-o', dest='outfile', type=str, default='stdout',
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
                        choices=['sw', 'gw', 'm'], default='sw',
                        help='Sets the method to use, defaults to sliding window \
                        (sw) but can also use a growing window (gw). Merge (m) \
                        option is typically used in a second or later pass, since \
                        it uses the full pre-existing segments of the input recipe \
                        and tries to merge consecutive turns if they are likely to \
                        be from the same speaker (also called "local clustering").')
    parser.add_argument('-d', dest='distance', type=str,
                        choices=['GLR', 'BIC', 'KL2'], default='GLR',
                        help='Sets the distance measure to use, defaults to \
                        Generalized Likelihood Ration (GLR) in sliding window or\
                        Bayesian Information Criterion (BIC) for growing window,\
                        or merging.\
                        Anyway both these and symmetric Kullback-Leibler (KL2) are \
                        possibilities.')
    parser.add_argument('-w', dest='winsize', type=float, default=5.0,
                        help='Specifies the windows size for detection in a \
                        sliding window approach, the minimum window in a growing \
                        window approach, or the maximum silence between windows \
                        when attempting to merge them, depending on the method \
                        chosen in the -m option. \
                        Default 5.0 sec.')
    parser.add_argument('-st', dest='winstep', type=float, default=0.5,
                        help='Specifies the windows moving (or maximum growing)\
                        step for detection, default 0.5 sec, should be set to\
                        more for growing windows methods if we wante better\
                        speed, maybe up to the window size.')
    parser.add_argument('-dws', dest='deltaws', type=float, default=0.05,
                        help='Specifies the minimum growing for growing windows\
                        methods. Defaults to 0.05 seconds.')
    parser.add_argument('-t', dest='threshold', type=float, default=0.0,
                        help='Specifies threshold distance for detection,\
                        default 0.0 (nonsensical handpicked, tune it except for\
                        BIC).')
    parser.add_argument('-l', dest='lambdac', type=float, default=1.3,
                        help='Lambda penalty weight for BIC, default 1.3')
    parser.add_argument('-tt', action='store_true',
                        help='If set, outputs all the decision thresholds in every \
                        window step, useful to define a proper threshold.')
    parser.add_argument('-dlr', action='store_true',
                        help='If set, disables lna renaming, so it keeps the lna \
                        original names (if there are two speakers in the same \
                        LNA, start and end line should be used for adaptation). \
                        By default it renames so that all segments have a \
                        a different LNA name.')
    args = parser.parse_args()

    # Process arguments
    print 'Reading recipe from:', args.recfile
    with open(args.recfile, 'r') as recfile:
        parsed_recipe = parse_recipe(recfile)

    print 'Reading feature files from:', args.feapath
    feapath = args.feapath

    if args.segpath:
        print 'Setting alignment segmentation files path to:', args.segpath
        print 'Segmentation files extension:', args.segext
    segpath = args.segpath
    segext = args.segext

    print 'Feature files extension:', args.feaext
    feaext = args.feaext

    if args.outfile != 'stdout':
        outfile = args.outfile
        print 'Writing output to:', args.outfile
        if segpath:
            segfile = op.splitext(op.basename(outfile))[0]
            segfile += '-seg' + op.splitext(outfile)[1]
            segfile = op.join(segpath, segfile)
            print 'Writing seg output to:', segfile
        else:
            segfile = False
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    rate = float(args.frame_rate)
    print 'Conversion rate set to frame rate:', rate

    if args.method == 'sw':
        print 'Using a fixed-size sliding window'
        dfun = dist_sw
    elif args.method == 'gw':
        print 'Using a growing window'
        dfun = dist_gw
        deltaws = np.floor(rate * args.deltaws)
        print 'Deltaws set to:', deltaws / rate, 'seconds'
    elif args.method == 'm':
        print 'Performing similar-segment merge'
        dfun = merge_rec

    if args.distance == 'GLR':
        print 'Using GLR as distance measure'
        dist = glr
    elif args.distance == 'BIC':
        print 'Using BIC as distance measure, lambda =', args.lambdac
        dist = bic
    elif args.distance == 'KL2':
        print 'Using KL2 as distance measure'
        dist = kl2

    winsize = args.winsize
    winstep = args.winstep
    winsize = np.floor(winsize * rate)
    winstep = np.floor(winstep * rate)
    if args.method != 'm':
        print 'Window size set to:', winsize / rate, 'seconds'
        print 'Window step set to:', winstep / rate, 'seconds'
    print 'Threshold distance:', args.threshold
    threshold = args.threshold

    lna_letter = 'a'
    lna_count = 0
    if args.dlr:
        print 'Disabling LNA renaming'

    # End of argument processing

    # Some useful metrics
    total_dist = 0
    max_dist = 0
    min_dist = sys.maxint
    total_windows = 0
    total_det_dist = 0
    max_det_dist = 0
    min_det_dist = sys.maxint
    total_segments = 0

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            if segfile:
                with open(segfile, 'w') as segf:
                    detect_changes(parsed_recipe, outf, segf)
            else:
                detect_changes(parsed_recipe, outf)

    else:
        detect_changes(parsed_recipe, outfile)

    print 'Useful metrics for determining the right threshold:'
    print '---------------------------------------------------'
    if total_windows > 0:
        print 'Average between windows distance:',\
              float(total_dist) / total_windows
    print 'Maximum between windows distance:', max_dist
    if min_dist < sys.maxint:
        print 'Minimum between windows distance:', min_dist
    print 'Total windows:', total_windows
    print 'Total segments:', total_segments + len(parsed_recipe)
    if total_segments > 0:
        print 'Average between detected segments distance:',\
              float(total_det_dist) / total_segments
    print 'Maximum between detected segments distance:', max_det_dist
    if min_det_dist < sys.maxint:
        print 'Minimum between detected segments distance:', min_det_dist
    print 'Total detected speaker changes:', total_segments
