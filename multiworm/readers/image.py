#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MWT image file manipulations
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import os.path
import glob
import re

def find(directory, basename):
    """
    Finds images in *directory* with the project-associated *basename* and 
    returns a dictionary with them indexed by time in seconds (and fractions 
    thereof).
    """
    image_files = {}
    image_re_mask = re.compile(re.escape(basename)
            + r'(?P<frame>[0-9]*)\.png$')

    for image in glob.iglob(os.path.join(directory, basename + '*.png')):
        match = image_re_mask.search(image)
        frame_num = match.group('frame')
        image_files[int('0' + frame_num) / 1000] = image

    return image_files
