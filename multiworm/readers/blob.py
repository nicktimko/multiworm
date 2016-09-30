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

from ..core import MWTBlobsError
from ..util import alternate, dtype

def find(directory, basename):
    """
    Find all \*.blobs files in the given *path* with the specified *basename*
    and verifies consecutiveness.  Returns a list of paths.
    """
    blobs_files = sorted(directory.glob(basename + '_?????k.blobs'))

    for i, fp in enumerate(blobs_files):
        expected_fn = '{}_{:05}k.blobs'.format(basename, i)
        if fp.name != expected_fn:
            raise MWTBlobsError("Experiment data missing a consecutive "
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

    i = None
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

    # check if blob was empty
    if i is None:
        return None

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

ENCODE_OFFSET = ord('0')
STEPS = np.array([(-1, 0), (1, 0), (0, -1), (0, 1)])

def decode_outline(start, n_points, encoded_outline):
    """
    Decodes the last four columns of data which represent the contour of
    the worm.

    Parameters
    ----------
    start : coordinate pair
        Starting X-Y coordinate of the encoded outline
    n_points : int
        Number of contour points encoded in *encoded_outline*
    encoded_outline : str
        The (non-standard) base64-encoded coordinate steps
    """
    if not n_points:
        raise ValueError('Empty data passed.')

    outline = np.empty((n_points + 1, 2), int)
    outline[0] = start
    remaining = n_points

    for ch in encoded_outline:
        byte = ord(ch) - ENCODE_OFFSET
        if not (0 <= byte <= 63):
            raise ValueError('({0}) is not in encoding range'.format(ch))

        for i in reversed(range(3)):
            if not remaining:
                break
            remaining -= 1

            step = STEPS[(byte >> 2*i) & 0b11]
            outline[n_points - remaining] = outline[n_points - remaining - 1] + step

    return outline

def encode_outline(outline):
    """
    Inverse of :func:`decode_outline`.  **NOT YET IMPLEMENTED**
    """

def decode_outline_line(blob_info, index):
    """
    Decodes the contour of the worm at a given *index* out of the data form
    returned by the parser as *blob_info*.  Basically, a more convienent
    interface for :func:`decode_outline`.
    """
    return decode_outline(
            blob_info['contour_start'][index],
            blob_info['contour_encode_len'][index],
            blob_info['contour_encoded'][index]
        )
