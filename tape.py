#!/usr/bin/env python
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six

import sys
import itertools
import argparse

import where
import multiworm
import tapeworm

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('test_set')
    args = parser.parse_args()

    plate = multiworm.Experiment(TEST_DATA_SETS[args.test_set])
    plate.add_summary_filter(multiworm.filters.summary_lifetime_minimum(120))
    plate.load_summary()
    plate.add_filter(multiworm.filters.relative_move_minimum(2))
    plate.load_blobs()

    print(len(plate.blobs_data))

def tapetest():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('data_set', help='The location of the data set. If '
        'names specified in a lookup file can be selected with a prefix of '
        '{0}.'.format(where.named_location))
    args = parser.parse_args()

    args.data_set = where.where(args.data_set)

    taper = tapeworm.Taper(args.data_set, verbosity=1)
    taper.load_data()

    for i, _ in enumerate(taper.segments()):
        print(i, end=' ')

if __name__ == '__main__':
    import cProfile as profile
    #command = "main()"
    command = "tapetest()"
    profile.runctx(command, globals(), locals(), filename="tape.profile")
    #main()
    #tapetest()

    sys.exit()
