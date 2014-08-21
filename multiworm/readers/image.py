#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MWT image file manipulations
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import pathlib
import re

import numpy as np

def find_nearest_index(seq, value):
    """
    Return the index of the value in the sequence that is closest to the
    given value
    """
    return (np.abs(np.array(seq)-value)).argmin()

def find_nearest(seq, value):
    """
    Return the value in the sequence that is closest to the given value
    """
    return seq[find_nearest_index(seq, value)]


class ImageFileOrganizer(dict):
    def __init__(self, *args, **kwargs):
        self.experiment = kwargs['experiment']
        del kwargs['experiment']
        super(ImageFileOrganizer, self).__init__(*args, **kwargs)

    def nearest(self, frame=None, time=None):
        if frame is None and time is None:
            raise ValueError("either the 'time' or 'frame' keyword argument "
                             "must be provided")
        if time is None:
            time = self.experiment.frame_times[frame - 1]

        image_time = find_nearest(list(six.iterkeys(self)), time)

        return time, self[image_time]


def find(directory, basename):
    """
    Finds images in *directory* with the project-associated *basename* and
    returns a dictionary with them indexed by time in seconds (and fractions
    thereof).
    """
    image_files = {}
    image_re_mask = re.compile(re.escape(basename)
            + r'(?P<frame>[0-9]*)\.png$')

    for image in directory.glob(basename + '*.png'):
        match = image_re_mask.search(str(image))
        frame_num = match.group('frame')
        image_files[int('0' + frame_num) / 1000] = image

    return image_files
