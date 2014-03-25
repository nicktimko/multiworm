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

        def fld(fieldname, *data, **kwargs):
            joiner = kwargs.get('joiner', ', ')
            try:
                datastr = joiner.join(
                    ('{0:.1f}' if type(pt) == float else '{0:d}').format(pt)
                    for pt in data)
            except TypeError:
                datastr = str(data)

            print(' {0:25s} | {1:s}'.format(fieldname, datastr))

        life_s = blob['time'][-1] - blob['time'][0]
        life_f = blob['frame'][-1] - blob['frame'][0]

        fld('Lifetime (s, frames)', life_s, life_f)
        fld('Time Range (s)', blob['time'][0], blob['time'][-1], joiner=' - ')
        fld('Frame Range', blob['frame'][0], blob['frame'][-1], joiner=' - ')
        fld('Found at', *blob['centroid'][0])
        fld('Lost at', *blob['centroid'][-1])


if __name__ == '__main__':
    sys.exit(main())
