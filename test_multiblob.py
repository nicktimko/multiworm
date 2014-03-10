#!/usr/bin/env python

from __future__ import print_function, unicode_literals, absolute_import
import sys
import tapeworm.tape as tape

import sys
import os.path
import json
import argparse

import multiworm
import where

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # parser = argparse.ArgumentParser(description='Get basic information '
    #     'about a particular blob.')

    # parser.add_argument('--data-set', default='%pics1', 
    #     help='The location of the data set. If names specified in a lookup '
    #     'file can be selected with a prefix of {0}.'.format(
    #         where.named_location))
    # parser.add_argument('--blob-id', type=int, help='The blob ID in the '
    #     'data set to summarize.')
    # parser.add_argument('-ht', '--head-and-tail', action='store_true')

    # args = parser.parse_args()

    data_set = where.where('%pics2')

    experiment = tape.MultiblobExperiment(data_set)
    experiment.load_summary()

    segments = [[4478, 4980, 7817], [4980, 7817], [7817], 7817]

    for seg in segments:
        patched_blob = experiment.parse_blob(seg)
        #patched_blob = experiment.parse_blob([4478, 1, 7817]) # should fail

        f_no = patched_blob['frame'][0]
        for frame in patched_blob['frame']:
            if f_no != frame:
                print("ERROR: Discontinuity from frame {0} to {1}".format(f_no-1, frame))
                f_no = frame
            f_no += 1
    print('Done.')


if __name__ == '__main__':
    sys.exit(main())