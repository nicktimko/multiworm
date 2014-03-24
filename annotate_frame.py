#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six

import sys
import argparse
import functools

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import multiworm
from multiworm.readers import blob as blob_reader
import where

# Derived from http://stackoverflow.com/a/2566508/194586
# However, I claim these as below the threshold of originality
def find_nearest_index(seq, value):
    return (np.abs(np.array(seq)-value)).argmin()
def find_nearest(seq, value):
    return seq[find_nearest_index(seq, value)]

def frame_parser(blob_lines, frame):
    """
    A lighter, probably quicker, parser to just get a single frame of 
    data out of a blob.
    """
    first_line = six.next(blob_lines)
    frame_offset = frame - int(first_line.split(' ', 1)[0])
    line = first_line

    # blindly consume as many lines as needed
    try:
        for _ in range(frame_offset):
            line = six.next(blob_lines)
    except MWTDataError:
        pass

    # parse the line and return
    blob = blob_reader.parse([line])
    if blob['frame'][0] != frame:
        raise multiworm.core.MWTDataError("Blob line offset failure")
    return blob

def frame_parser_spec(frame):
    return functools.partial(frame_parser, frame=frame)

def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Get basic information '
        'about a particular blob.')

    parser.add_argument('data_set', help='The location of the data set. If '
        'names specified in a lookup file can be selected with a prefix of '
        '{0}.'.format(where.named_location))
    parser.add_argument('time', type=float, help='The time to display.  '
        'Coerced to the nearest available image if no exact match.')

    args = parser.parse_args(argv[1:])

    args.data_set = where.where(args.data_set)

    experiment = multiworm.Experiment(args.data_set)
    experiment.load_summary()

    # find the closest still to the given time
    time = find_nearest(list(experiment.image_files.keys()), args.time)
    print("- Found image at {0:.2f} s ({1:+.2f} s relative to specified "
          "time)".format(time, time - args.time))
    image_file = experiment.image_files[time]
    print(image_file)
    img = mpimg.imread(image_file)

    # find the closest frame to the derived still time
    frame = find_nearest_index(experiment.frame_times, time) + 1
    frame_time = experiment.frame_times[frame - 1]
    print("- Nearest frame at {0:.2f} s ({1:+.2f} s "
          "relative to image)".format(frame_time, frame_time - time))

    bids = experiment.blobs_in_frame(frame)
    print("- {0} blobs tracked on frame {1}".format(len(bids), frame))

    outlines = []
    parser = frame_parser_spec(frame)
    for bid in bids:
        blob = experiment.parse_blob(bid, parser)
        outline = blob_reader.decode_outline(
                blob['contour_start'][0],
                blob['contour_encode_len'][0],
                blob['contour_encoded'][0],
            )
        outlines.append(outline)

    f, ax = plt.subplots()
    ax.imshow(img.T, cmap=plt.cm.Greys_r)
    for outline in outlines:
        ax.plot(*outline.T)

    plt.show()
    return

if __name__ == '__main__':
    sys.exit(main())
