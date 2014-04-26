# -*- coding: utf-8 -*-
"""
Assess the amount of noise present in an experiment
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import argparse
import itertools
import json

import numpy as np

import multiworm
import multiworm.analytics
import where

def main():
    parser = argparse.ArgumentParser(description='Get basic information '
        'about an experiment.')

    parser.add_argument('data_set', help='The location of the data set. If '
        'names specified in a lookup file can be selected with a prefix of '
        '{0}.'.format(where.named_location).replace('%', '%%'))
    parser.add_argument('-l', '--limit', type=int, help='Limit the number '
        'of blobs to process')
    parser.add_argument('-p', '--plot', action='store_true', help='Show a '
        'plot (if supported by another command)')
    parser.add_argument('-j', '--json', action='store_true', help='Dump '
        'data to a JSON.')

    args = parser.parse_args()

    args.data_set = where.where(args.data_set)

    experiment = multiworm.Experiment(args.data_set)
    experiment.load_summary()

    experiment.add_summary_filter(multiworm.filters.summary_lifetime_minimum(120))
    experiment.add_filter(multiworm.filters.relative_move_minimum(2))

    if args.limit:
        blob_gen = itertools.islice(experiment.good_blobs(), args.limit)
    else:
        blob_gen = experiment.good_blobs()

    speed_config = {
        'smoothing': ('sgolay', 71, 5),
        'percentiles': [10, 20, 50, 80, 90],
    }

    noise_est = multiworm.analytics.NoiseEstimator()
    speed_est = multiworm.analytics.SpeedEstimator(**speed_config)

    analyzer = multiworm.analytics.ExperimentAnalyzer()
    analyzer.add_analysis_method(noise_est)
    #analyzer.add_analysis_method(speed_est)

    analyzer.analyze(blob_gen)

    data = analyzer.result_dict()

    if args.json:
        print(json.dumps(data, indent=4))

    else:
        print('Mean X/Y              : ', data['noise']['mean_xy'])
        print('Standard Deviation X/Y: ', data['noise']['std_dev_xy'])

    if args.plot:
        import matplotlib.pyplot as plt

        f, axs = plt.subplots(ncols=2)
        f.suptitle('Normal summary statistics for frame-by-frame centroid steps')
        for ax, data, title in zip(axs, [data['noise']['means'], data['noise']['std_devs']],
                ['X/Y means', 'X/Y stddev']):
            ax.scatter(*zip(*data))
            ax.set_title(title)
            ax.axvline()
            ax.axhline()
            ax.axis('equal')

        axs[1].set_xlim(left=0)
        axs[1].set_ylim(bottom=0)

        plt.show()

if __name__ == '__main__':
    main()
