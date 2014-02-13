#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Load data from a Multi-Worm Tracker experiment
"""
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

from collections import defaultdict

from ..util import alternate

def parse(lines):
    """
    Consumes a provided *lines* iterable and generates two dictionaries; the 
    first containing the basic information, packaged in lists with keys:

      * `frame`: Video frame number
      * `time`: Real time since beginning of experiment
      * `centroid`: Blob center of "mass"
      * `area`: Area of blob
      * `std_vector`:
      * `std_ortho`:
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
    blob_geometry = defaultdict(list, {})

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
            blob_geometry['midline'].append(tuple(zip(*alternate([int(x) for x in ld[1].split()]))))

            # contour data
            ldc = ld[3].split()
            blob_geometry['contour_start'].append((int(ldc[0]), int(ldc[1])))
            blob_geometry['contour_encode_len'].append(int(ldc[2]))
            blob_geometry['contour_encoded'].append(ldc[3])
        else:
            blob_geometry['midline'].append(None)
            blob_geometry['contour_start'].append((0, 0))
            blob_geometry['contour_encode_len'].append(None)
            blob_geometry['contour_encoded'].append(None)

    # prevent referencing non-existant fields
    blob_info.default_factory = None
    blob_geometry.default_factory = None

    # verify everything is the same length
    frames = len(blob_info['frame'])
    assert all(len(v) == frames for v in blob_info.values())
    assert all(len(v) == frames for v in blob_geometry.values())

    return blob_info, blob_geometry
