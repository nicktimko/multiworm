#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import zip, range, map

import sys
import os.path
import argparse

import numpy as np

import multiworm
import where
import blob_info

def longest_10(experiment, ten=10):
    blob_lifespan = [(blob['bid'], blob['died'] - blob['born']) for blob in experiment.summary]
    blob_lifespan = sorted(blob_lifespan, key=lambda x: x[1], reverse=True)
    return blob_lifespan[:ten]

def assess_noise(experiment, npoints=200, plot=False):
    xmeans, ymeans = [], []
    xsds, ysds = [], []

    for n, blob in enumerate(longest_10(experiment, ten=npoints), start=1):
        bid, life = blob

        blob = experiment.parse_blob(bid)
        if blob is None:
            continue

        steps = blob_info.centroid_steps(blob['centroid'])
        (xmean, xsd), (ymean, ysd) = blob_info.centroid_stats(steps)

        xmeans.append(xmean)
        xsds.append(xsd)
        ymeans.append(ymean)
        ysds.append(ysd)

    means = [np.mean(v) for v in [xmeans, xsds, ymeans, ysds]]

    if plot:
        import matplotlib.pyplot as plt
        f, axs = plt.subplots(ncols=2)
        f.suptitle('Normal summary statistics for frame-by-frame centroid steps')
        for ax, data, title in zip(axs, [[xmeans, ymeans], [xsds, ysds]], 
                ['X/Y means', 'X/Y stddev']):
            ax.scatter(*data)
            ax.set_title(title)
            ax.axvline()
            ax.axhline()

        axs[1].set_xlim(left=0)
        axs[1].set_ylim(bottom=0)

    return means

def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Get basic information '
        'about an experiment.')

    parser.add_argument('data_set', help='The location of the data set. If '
        'names specified in a lookup file can be selected with a prefix of '
        '{0}.'.format(where.named_location).replace('%', '%%'))
    parser.add_argument('-n', '--noise', action='store_true', 
        help='Estimate the amount of noise present in the centroid data.  '
        'Plot available.')
    parser.add_argument('-l', '--longest', type=int, help='Display the '
        'longest-lived blobs', default=10)
    parser.add_argument('-p', '--plot', action='store_true', help='Show a '
        'plot (if supported by another command)')

    args = parser.parse_args()

    args.data_set = where.where(args.data_set)

    experiment = multiworm.Experiment(args.data_set)
    experiment.load_summary()

    print('Experiment summary file: {}'.format(experiment.summary_file))
    print('Number of blobs        : {}'.format(len(experiment.summary)))

    if args.noise:
        means = assess_noise(experiment, plot=args.plot)

        print('X mean of means/stddevs: {:0.3e} \u00B1 {:0.3e}'.format(*means[0:2]))
        print('Y mean of means/stddevs: {:0.3e} \u00B1 {:0.3e}'.format(*means[2:4]))

    if args.longest:
        print('   {:>5s} | {}'.format('ID', 'Life (s)'))
        print('  {:->7s}+{:-<10s}'.format('', ''))
        for bid, lifespan in longest_10(experiment, args.longest):
            print('   {:5d} | {:7.2f}'.format(bid, lifespan))


    if args.plot:
        import matplotlib.pyplot as plt
        plt.show()

if __name__ == '__main__':
    sys.exit(main())
