#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import zip, range, map

import sys
import argparse
import numbers

import numpy as np
import scipy.optimize as spo
import scipy.stats as sps
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

import multiworm
import where

def head_and_tail(linegen):
    try:
        head = tail = six.next(linegen)
    except StopIteration:
        return [] # linegen has zero length
    for tail in linegen:
        assert not tail.startswith('%')
    if head != tail:
        return [head, tail]
    else:
        return [head]

def fit_gaussian(x, num_bins=200):
    # some testdata has no variance whatsoever, this is escape clause
    if abs(max(x) - min(x)) < 1e-5:
        print('fit_gaussian exit')
        return max(x), 1

    n, bin_edges = np.histogram(x, num_bins, normed=True)
    bincenters = [0.5 * (bin_edges[i + 1] + bin_edges[i]) for i in range(len(n))]

    # Target function
    fitfunc = lambda p, x: mlab.normpdf(x, p[0], p[1])

    # Distance to the target function 
    errfunc = lambda p, x, y: fitfunc(p, x) - y

    # Initial guess for the parameters
    mu = np.mean(x)
    sigma = np.std(x)
    p0 = [mu, sigma]
    p1, success = spo.leastsq(errfunc, p0[:], args=(bincenters, n))
    # weirdly if success is an integer from 1 to 4, it worked.
    if success in [1,2,3,4]:
        mu, sigma = p1
        return mu, sigma
    else:
        return None

def centroid_stats(steps):
    stats = []
    for data in steps:
        stats.append(fit_gaussian(data))
    return stats

def centroid_steps(centroid):
    xy = zip(*centroid)
    dxy = [np.diff(d) for d in xy]
    return dxy

def step_distribution(centroid):
    f, ax = plt.subplots()
    steps = centroid_steps(centroid)

    stats = centroid_stats(steps)
    for direction, color, meansd, data in zip(['X', 'Y'], ['red', 'green'], stats, steps):
        mean, sd = meansd
        print(' {0:25s} | {1:0.2e}, {2:0.2e}'.format(direction + ' stddev, mean', sd, mean))
        ax.hist(data, 500, histtype='stepfilled', color=color, alpha=0.5, normed=True)
        norm_x = np.linspace(-4, 4, 100) * sd + mean
        norm_y = sps.norm(mean, sd).pdf(norm_x)
        ax.plot(norm_x, norm_y, color=color, ls='--', lw=3)

def spectrogram(centroid):
    f, axs = plt.subplots(2, 2, sharex=True)
    for ax, data in zip(axs, zip(*centroid)):
        #import pdb;pdb.set_trace()
        ax1, ax2 = ax
        ax1.plot(np.arange(len(data))/25, data)
        ax2.specgram(data, NFFT=512, Fs=25)

def excise_frames(blob, start, stop):
    first_frame = blob['frame'][0]
    start_idx = start - first_frame
    end_idx = stop - first_frame
    if start_idx < 0 or end_idx > len(blob['frame']):
        raise ValueError('Start/stop frames outside of bounds')
    return blob['centroid'][start_idx:end_idx]

def fld(fieldname, *data, **kwargs):
    joiner = kwargs.get('joiner', ', ')
    try:
        datastr = joiner.join(
            ('{0:.1f}' if isinstance(pt, numbers.Real) else '{0:d}').format(pt)
            for pt in data)
    except TypeError:
        datastr = str(data)

    print(' {0:25s} | {1:s}'.format(fieldname, datastr))

def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Get basic information '
        'about a particular blob.')

    parser.add_argument('data_set', help='The location of the data set. If '
        'names specified in a lookup file can be selected with a prefix of '
        '{0}.'.format(where.named_location))
    parser.add_argument('blob_id', type=int, help='The blob ID in the '
        'data set to summarize.')
    parser.add_argument('-ht', '--head-and-tail', action='store_true')
    parser.add_argument('--xy', action='store_true', help='Plot X and Y '
        'coordinates for the blob')
    parser.add_argument('--spec', action='store_true', help='Spectogram')
    #parser.add_argument('--show', action='store_true', help='Try to show the blob using images')
    parser.add_argument('--dist', action='store_true', help='Distribution of steps')
    parser.add_argument('--frames', type=int, nargs=2, help='Start/stop frames')

    args = parser.parse_args()

    args.data_set = where.where(args.data_set)

    experiment = multiworm.Experiment(args.data_set)
    experiment.load_summary()
    if args.blob_id not in experiment.bs_mapping:
        print('Blob ID {0} not found.'.format(args.blob_id), file=sys.stderr)
        sys.exit(1)

    file_no, offset = experiment.summary[['file_no', 'offset']][experiment.bs_mapping[args.blob_id]]

    if args.head_and_tail:
        for line in experiment.parse_blob(args.blob_id, head_and_tail):
            print(line, end='')

    else:
        blob = experiment.parse_blob(args.blob_id)
        if blob is None:
            print("Blob ID {} exists, but has no data.".format(args.blob_id), 
                file=sys.stderr)
            return

        print('Data in blobs file number {0}, starting at byte {1}'.format(file_no, offset))
        print('Path: {0}'.format(experiment.blobs_files[file_no]))
        print(' {0:^25s} | {1:^30s} '.format('Field', 'Data'))
        print(' ' + '-'* 65)

        life_s = blob['time'][-1] - blob['time'][0]
        life_f = blob['frame'][-1] - blob['frame'][0]

        fld('Lifetime (s, frames)', life_s, life_f)
        fld('Time Range (s)', blob['time'][0], blob['time'][-1], joiner=' - ')
        fld('Frame Range', blob['frame'][0], blob['frame'][-1], joiner=' - ')
        fld('Found at', *blob['centroid'][0])
        fld('Lost at', *blob['centroid'][-1])

        #if args.show:
        #    pass
        if args.xy:
            centroid = excise_frames(blob, *args.frames) if args.frames else blob['centroid']

            if args.spec:
                spectogram(centroid)

            elif args.dist:
                step_distribution(centroid)

            else: # show X and Y over frames
                f, axs = plt.subplots(2, sharex=True)
                for ax, data in zip(axs, zip(*centroid)):
                    ax.plot(data)

            plt.show()

if __name__ == '__main__':
    sys.exit(main())
