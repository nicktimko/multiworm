from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six

import sys
import itertools
import argparse
#import gc
import time
#import resource

import multiworm

TEST_DATA_SETS = {
    '%pics1': '/home/projects/worm_movement/Data/MWT_RawData/20130702_135704',
    '%pics2': '/home/projects/worm_movement/Data/MWT_RawData/20130702_135652',
    '%test1': 'C:\\Users\\Nick\\Local HG\\TapeWorms\\Data\\20130320_102310',
    '%test2': 'C:\\Users\\Nick\\Local HG\\TapeWorms\\Data\\20130321_123510',
}


def memprint():
    #rusage = resource.getrusage(resource.RUSAGE_SELF)
    #peak = rusage.ru_maxrss/1024.0
    #m = memory_usage()
    #peak = m['peak']/1024
    #rss = m['rss']/1024
    #return 'Peak: {:6.1f} MB'.format(peak)
    pass

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('test_set')
    args = parser.parse_args()

    plate = multiworm.Experiment(TEST_DATA_SETS[args.test_set])
    plate.add_summary_filter(multiworm.filters.summary_lifetime_minimum(120))
    plate.load_summary()

    ids = []
    t = time.time()
    for blob in itertools.islice(plate.good_blobs(), 5):
        now = time.time()
        t, tdelta = now, now - t

        bid, bdata = blob
        print(memprint(), 'ID: {:5d}, t: {:7.1f} ms'.format(bid, tdelta * 1000))
        ids.append(bid)
        blob, bdata = None, None

    print(ids)

if __name__ == '__main__':
    import cProfile as profile
    command = 'main()'
    profile.runctx(command, locals=locals(), globals=globals(), filename='test_read.profile')
