from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six

import sys
import argparse
import multiworm
import multiworm.experiment.blob as meb

TEST_DATA_SETS = {
    '%pics1': '/home/projects/worm_movement/Data/MWT_RawData/20130702_135704',
    '%pics2': '/home/projects/worm_movement/Data/MWT_RawData/20130702_135652',
}

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('test_set')
    args = parser.parse_args()

    plate = multiworm.Experiment(TEST_DATA_SETS[args.test_set])
    #plate.add_summary_filter(multiworm.filters.minimum_time(120))
    plate.load_summary()

    print(len(plate.blobs_summary))
    bid, v = six.next(six.iteritems(plate.blobs_summary))
    print(bid, v)
    # blob_file, offset = v['location']
    # print(plate.blobs_files[blob_file])
    #plate.parse_blob(bid)
    print(plate.parse_blob(1187))


if __name__ == '__main__':
    sys.exit(main())
