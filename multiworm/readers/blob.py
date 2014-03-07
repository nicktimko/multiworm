#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MWT blob file manipulations
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import os.path
import glob
from collections import defaultdict

import numpy as np

from ..core import MWTDataError
from ..util import alternate, dtype

def find(directory, basename):
    """
    Find all \*.blobs files in the given *path* with the specified *basename* 
    and verifies consecutiveness.  Returns a list of paths.
    """
    blobs_files = sorted(glob.iglob(os.path.join(
            directory, basename + '_?????k.blobs')))

    for i, fn in enumerate(blobs_files):
        expected_fn = '{}_{:05}k.blobs'.format(basename, i)
        if not fn.endswith(expected_fn):
            raise MWTDataError("Experiment data missing a consecutive "
                    "blobs file. ({})".format(expected_fn))

    return blobs_files

def parse(lines):
    """
    Consumes a provided *lines* iterable and generates two dictionaries; the 
    first containing the basic information, packaged in lists with keys:

      * `frame`: Image number
      * `time`: Real time since beginning of experiment
      * `centroid`: Blob center of mass
      * `area`: Pixel area of blob
      * `std_vector`: Vector pointing along the long axis of the object with 
        length equal to the standard deviation of the pixels along that 
        axis.
      * `std_ortho`: The standard deviation of pixel positions orthogonal 
        to the above vector
      * `size`: Rectangular size of the blob as determined by MWT

    The other dictionary contains geometry information, and can be missing 
    in some frames.  If missing, `contour_encode_len` will be None.  Fields 
    include:

      * `midline`: 11 coordinates relative to the position of the centroid
        that represent MWT's initial guess at the worm shape
      * `contour_start`: Start coordinates of the encoded contour.
      * `contour_encode_len`: Length of the encoded contour.  Required due to
        the last encoded character being ambiguous as to how many points it
        actually encodes.
      * `contour_encoded`: the base64esque encoded outline.  Three steps are
        encoded per character, each one of up, down, left, or right (using 2
        bits).
    """
    blob_info = defaultdict(list, {})

    for i, line in enumerate(lines):
        ld = line.split('%')

        # parse the first block with the generic stats
        lda = ld[0].split()
        blob_info['frame'].append(int(lda[0]))
        blob_info['time'].append(float(lda[1]))
        blob_info['centroid'].append((float(lda[2]), float(lda[3])))
        blob_info['area'].append(int(lda[4]))
        blob_info['std_vector'].append((float(lda[5]), float(lda[6])))
        blob_info['std_ortho'].append(float(lda[7]))
        blob_info['size'].append((float(lda[8]), float(lda[9])))

        # if there are geometry sections, parse them too.
        if len(ld) == 4:
            blob_info['midline'].append(tuple(zip(*alternate([int(x) for x in ld[1].split()]))))

            # contour data
            ldc = ld[3].split()
            blob_info['contour_start'].append((int(ldc[0]), int(ldc[1])))
            blob_info['contour_encode_len'].append(int(ldc[2]))
            blob_info['contour_encoded'].append(ldc[3])
        else:
            blob_info['midline'].append(None)
            blob_info['contour_start'].append((0, 0))
            blob_info['contour_encode_len'].append(None)
            blob_info['contour_encoded'].append(None)

    # prevent referencing non-existant fields
    blob_info.default_factory = None

    # verify everything is the same length
    frames = len(blob_info['frame'])
    assert all(len(v) == frames for v in blob_info.values())

    return blob_info

INFO_FIELDS = dtype([
        ('frame', 'int32'),
        ('time', 'float'),
        ('centroid', '2float'),
        ('area', 'int32'),
        ('std_vector', '2float'),
        ('std_ortho', 'float'),
        ('size', '2float'),
    ])
GEO_FIELDS = dtype([
        ('midline', '(11, 2)int8'),
        ('contour_start', '2int32'),
        ('contour_encode_len', 'int32'),
        ('contour_encoded', 'object'),
    ])

def parse_np(lines):
    ''
    """
    **UNIMPLEMENTED**

    Consumes a provided *payload* string and generates two arrays for each
    block of data in it. The first contains the basic information,
    guaranteed in each frame.  Column fields in first array:

      * `frame`: Video frame number
      * `time`: Real time since beginning of experiment
      * `centroid`: Blob center of "mass"
      * `area`: Area of blob
      * `std_vector`:
      * `std_ortho`:
      * `size`: Rectangular size of the blob as determined by MWT

    The other array contains geometry information, and can come in and out
    beween frames.  If missing, `contour_encode_len` will equal 0.  Column
    fields include:

      * `midline`: 11 coordinates relative to the position of the centroid
        that represent MWT's initial guess at the worm shape
      * `contour_start`: Start coordinates of the encoded contour.
      * `contour_encode_len`: Length of the encoded contour.  Required due to
        the last encoded character being ambiguous as to how many points it
        actually encodes.
      * `contour_encoded`: the base64esque encoded outline.  Three steps are
        encoded per character, each one of up, down, left, or right (using 2
        bits).

    """
    lines = list(lines)
    blob_info = np.zeros(len(lines), dtype=INFO_FIELDS + GEO_FIELDS)

    for i, line in enumerate(lines):
        ld = line.split('%')

        # parse the first block with the generic stats
        lda = ld[0].split()
        blob_info[i]['frame'] = lda[0]
        blob_info[i]['time'] = lda[1]
        blob_info[i]['centroid'][0] = lda[2]
        blob_info[i]['centroid'][1] = lda[3]
        blob_info[i]['area'] = lda[4]
        blob_info[i]['std_vector'][0] = lda[5]
        blob_info[i]['std_vector'][1] = lda[6]
        blob_info[i]['std_ortho'] = lda[7]
        blob_info[i]['size'][0] = lda[8]
        blob_info[i]['size'][1] = lda[9]

        # if there are geometry sections, parse them too.
        if len(ld) == 4:
            # second block contains 11 x-y coordinates
            blob_info[i]['midline'][:] = np.array(
                    ld[1].split(), dtype='int8').reshape(11, 2)
            # third has contour information
            ldc = ld[3].split()
            blob_info[i]['contour_start'][0] = ldc[0]
            blob_info[i]['contour_start'][1] = ldc[1]
            blob_info[i]['contour_encode_len'] = ldc[2]
            blob_info[i]['contour_encoded'] = ldc[3]

    return blob_info
