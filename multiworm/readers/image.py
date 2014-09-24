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
import warnings

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

    def _frame_time(self, frame):
        return self.experiment.frame_times[max(0, int(frame) - 1)]

    def nearest(self, **kwargs):
        """
        Given keyword argument 'frame' or 'time', return the path of the
        nearest image and the time it was taken (as a tuple)
        """
        frame = kwargs.get('frame', None)
        time = kwargs.get('time', None)

    #def nearest(self, *, frame=None, time=None): # in Py3 we could do this
        if frame is None and time is None:
            raise ValueError("either the 'time' or 'frame' keyword argument "
                             "must be provided")
        if time is None:
            # warn against rogue floats
            if int(frame) != frame:
                warnings.warn('non-integer passed to nearest() as a frame', Warning)

            time = self._frame_time(frame)

        image_time = find_nearest(list(six.iterkeys(self)), time)

        return self[image_time], image_time

    def spanning(self, **kwargs):
        """
        spanning(times=[t0, tN])
        spanning(frames=[f0, fN])

        Returns a list of filenames encompassing the desired time or frame
        range. Guaranteed to return at least one filename.
        """
        if 'frames' in kwargs:
            times = (self._frame_time(f) for f in kwargs['frames'])
        else:
            times = kwargs['times']

        keytimes = sorted(self)

        try:
            istart, iend = (find_nearest_index(keytimes, t) for t in times)
        except ValueError:
            raise ValueError('Only two frames or times values are accepted')

        return [self[keytimes[i]] for i in range(istart, iend + 1)]

        #find_nearest_index()
        #return sorted(self[t] for t in six.iterkeys(self) if key.start <= t <= key.stop)

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
