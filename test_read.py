#!/usr/bin/env python
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six

import sys
import itertools
import argparse
#import gc
import time
import resource

import multiworm

TEST_DATA_SETS = {
    '%pics1': '/home/projects/worm_movement/Data/MWT_RawData/20130702_135704',
    '%pics2': '/home/projects/worm_movement/Data/MWT_RawData/20130702_135652',
    '%test1': 'C:\\Users\\Nick\\Local HG\\TapeWorms\\Data\\20130320_102310',
    '%test2': 'C:\\Users\\Nick\\Local HG\\TapeWorms\\Data\\20130321_123510',
}


def memory_usage():
    """Memory usage of the current process in kilobytes."""
    status = None
    result = {'peak': 0, 'rss': 0}
    try:
        # This will only work on systems with a /proc file system
        # (like Linux).
        status = open('/proc/self/status')
        for line in status:
            parts = line.split()
            key = parts[0][2:-1].lower()
            if key in result:
                result[key] = int(parts[1])
    finally:
        if status is not None:
            status.close()
    return result

def memprint():
    m = memory_usage()
    peak = m['peak']/1024
    rss = m['rss']/1024
    return 'Peak: {0:6.1f} MB, Current: {1:6.1f} MB'.format(peak, rss)

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('test_set')
    args = parser.parse_args()

    plate = multiworm.Experiment(TEST_DATA_SETS[args.test_set])
    plate.add_summary_filter(multiworm.filters.summary_lifetime_minimum(120))
    plate.load_summary()

    ids = []
    t = time.time()
    for blob in itertools.islice(plate.good_blobs(), 50):
        now = time.time()
        t, tdelta = now, now - t

        bid, bdata = blob
        print(memprint(), 'ID: {0:5d}, t: {1:7.1f} ms'.format(bid, tdelta * 1000))
        ids.append(bid)
        blob, bdata = None, None

    print(ids)

if __name__ == '__main__':
    import cProfile as profile
    command = 'main()'
    profile.runctx(command, locals=locals(), globals=globals(), filename='test_read.profile')
