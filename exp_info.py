#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import zip, range, map

import sys
import argparse

import numpy.lib.recfunctions as rfn

import multiworm
import where

def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Get basic information '
        'about an experiment.')

    parser.add_argument('data_set', help='The location of the data set. If '
        'names specified in a lookup file can be selected with a prefix of '
        '{0}.'.format(where.named_location))

    args = parser.parse_args()

    args.data_set = where.where(args.data_set)

    experiment = multiworm.Experiment(args.data_set)
    experiment.load_summary()

    print('Experiment summary file: {}'.format(experiment.summary_file))
    print('Number of blobs        : {}'.format(len(experiment.summary)))
    
    blob_lifespan = [(blob['bid'], blob['died'] - blob['born']) for blob in experiment.summary]
    blob_lifespan = sorted(blob_lifespan, key=lambda x: x[1], reverse=True)

    print('Top 10 longest living blobs:')
    for n, blob in enumerate(blob_lifespan[:10], start=1):
        print(' {:>2d}. {:<5d} ({} s)'.format(n, blob[0], blob[1]))
    
    # print(' {0:^25s} | {1:^30s} '.format('Field', 'Data'))
    # print(' ' + '-'* 65)

    # def fld(fieldname, *data, **kwargs):
    #     joiner = kwargs.get('joiner', ', ')
    #     try:
    #         datastr = joiner.join(
    #             ('{0:.1f}' if type(pt) == float else '{0:d}').format(pt)
    #             for pt in data)
    #     except TypeError:
    #         datastr = str(data)

    #     print(' {0:25s} | {1:s}'.format(fieldname, datastr))

    # life_s = blob['time'][-1] - blob['time'][0]
    # life_f = blob['frame'][-1] - blob['frame'][0]

    # fld('Lifetime (s, frames)', life_s, life_f)
    # fld('Time Range (s)', blob['time'][0], blob['time'][-1], joiner=' - ')
    # fld('Frame Range', blob['frame'][0], blob['frame'][-1], joiner=' - ')
    # fld('Found at', *blob['centroid'][0])
    # fld('Lost at', *blob['centroid'][-1])

if __name__ == '__main__':
    sys.exit(main())
