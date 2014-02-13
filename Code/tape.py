from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from future.builtins import *

import sys
import argparse
import multiworm

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

if __name__ == '__main__':
    sys.exit(main())
