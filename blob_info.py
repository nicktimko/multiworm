#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six

import sys
import argparse

import multiworm
import where

def head_and_tail(linegen):
    head = six.next(linegen)
    for tail in linegen:
        assert not tail.startswith('%')
    return head, tail

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

    args = parser.parse_args()

    args.data_set = where.where(args.data_set)

    experiment = multiworm.Experiment(args.data_set)
    experiment.load_summary()
    if args.blob_id not in experiment.bs_mapping:
        print('Blob ID {} not found.'.format(args.blob_id), file=sys.stderr)
        sys.exit(1)

    file_no, offset = experiment.blobs_summary[['file_no', 'offset']][experiment.bs_mapping[args.blob_id]]
    print('Data in blobs file number {}, starting at byte {}'.format(file_no, offset))
    print('Path: {}'.format(experiment.blobs_files[file_no]))

    if args.head_and_tail:
        head, tail = experiment.parse_blob(args.blob_id, head_and_tail)
        print(head)
        print(tail)
    else:
        blob = experiment.parse_blob(args.blob_id)
        print(' {:^25s} | {:^30s} '.format('Field', 'Data'))
        print(' ' + '-'* 65)

        def fld(fieldname, *data, **kwargs):
            joiner = kwargs.get('joiner', ', ')
            try:
                datastr = joiner.join(
                    ('{:.1f}' if type(pt) == float else '{:d}').format(pt)
                    for pt in data)
            except TypeError:
                datastr = str(data)

            print(' {:25s} | {:s}'.format(fieldname, datastr))

        life_s = blob['time'][-1] - blob['time'][0]
        life_f = blob['frame'][-1] - blob['frame'][0]

        fld('Lifetime (s, frames)', life_s, life_f)
        fld('Time Range (s)', blob['time'][0], blob['time'][-1], joiner=' - ')
        fld('Frame Range', blob['frame'][0], blob['frame'][-1], joiner=' - ')
        fld('Found at', *blob['centroid'][0])
        fld('Lost at', *blob['centroid'][-1])


if __name__ == '__main__':
    sys.exit(main())

'''

 Loading... [ ####---------------------------------------------- ] 99/1149 (8.6%)      
    1 --> 1323  : f=217, d=292.0, log_score=1e-100
    1 --> 1535  : f=443, d=568.4, log_score=0.000201218967721
    8 --> 1323  : f=217, d=292.0, log_score=1e-100
    8 --> 1535  : f=443, d=568.4, log_score=0.000201218967721
   12 --> 1323  : f=217, d=292.0, log_score=1e-100
   12 --> 1535  : f=443, d=568.4, log_score=0.000201218967721
   16 --> 1323  : f=217, d=292.0, log_score=1e-100
   16 --> 1535  : f=443, d=568.4, log_score=0.000201218967721
   17 --> 1323  : f=217, d=292.0, log_score=1e-100
   17 --> 1535  : f=443, d=568.4, log_score=0.000201218967721
   23 --> 1323  : f=217, d=292.0, log_score=1e-100
   23 --> 1535  : f=443, d=568.4, log_score=0.000201218967721
   24 --> 1323  : f=217, d=292.0, log_score=1e-100

'''