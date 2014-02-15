from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six

import sys
import itertools
import argparse
import gc

import multiworm

TEST_DATA_SETS = {
    '%pics1': '/home/projects/worm_movement/Data/MWT_RawData/20130702_135704',
    '%pics2': '/home/projects/worm_movement/Data/MWT_RawData/20130702_135652',
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
    return 'Peak: {:6.1f} MB, Current: {:6.1f} MB'.format(peak, rss)

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('test_set')
    args = parser.parse_args()

    plate = multiworm.Experiment(TEST_DATA_SETS[args.test_set])
    plate.add_summary_filter(multiworm.filters.lifetime_minimum(120))
    plate.load_summary()

    ids = []
    for blob in plate.good_blobs():
        bid, bdata = blob
        print(memprint(), bid)
        ids.append(bid)
        blob, bdata = None, None

    print(ids)

if __name__ == '__main__':
    sys.exit(main())
