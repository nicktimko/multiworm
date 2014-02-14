from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six

import sys
import itertools
import argparse

import multiworm
import tapeworm

TEST_DATA_SETS = {
    '%pics1': '/home/projects/worm_movement/Data/MWT_RawData/20130702_135704',
    '%pics2': '/home/projects/worm_movement/Data/MWT_RawData/20130702_135652',
}

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('test_set')
    args = parser.parse_args()

    plate = multiworm.Experiment(TEST_DATA_SETS[args.test_set])
    plate.add_summary_filter(multiworm.filters.lifetime_minimum(120))
    plate.load_summary()
    plate.add_filter(multiworm.filters.relative_move_minimum(2))
    plate.load_blobs()

    print(len(plate.blobs_data))

def tapetest():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('test_set')
    args = parser.parse_args()

    taper = tapeworm.Taper(TEST_DATA_SETS[args.test_set])

    #blob_generator = 
    #taper.plate.good_blobs = lambda: itertools.islice(taper.plate.good_blobs(), 4)

    taper.process(show_progress=True)

if __name__ == '__main__':
    import cProfile as profile
    #command = "main()"
    command = "tapetest()"
    profile.runctx(command, globals(), locals(), filename="tape.profile")
    #main()
    #tapetest()

    sys.exit()
