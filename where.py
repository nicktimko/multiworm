#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six

import sys
import os.path
import json
import argparse

named_location = '%'

default_location = '/home/projects/worm_movement/Data/MWT_RawData'

data_file = os.path.join(os.path.dirname(__file__), 'data_sets.json')
with open(data_file, 'r') as f:
    data_sets = json.load(f)

def where(data_set):
    """
    Converts a short dataset name into the full path.  There are a couple 
    techniques used to find or refer to a data set, any of which can be used.

    1. Named data set lookup in JSON.  If the provided string starts with 
       a special character (``%``), the full path is looked up in a JSON using 
       the remainder of the string.  Failure will raise a KeyError.

    2. Backup states.  If the provided string starts with ``bak^XY^``, where 
       ``X`` is one of ``d``, ``w``, or ``m`` (for daily, weekly, and 
       monthly, respectively), and Y is a number, the returned path will 
       point to the respective backup.  e.g. ``bak^d5^20120101_000000`` will 
       be transformed into the path pointing at the ``daily.5`` backup 
       dataset version.

    3. Explicit dataset location.  If the string provided is a valid path, 
       the function will return the same string.

    4. Implicit dataset location.  If none of the above apply, the string is 
       appended to the standard location for datasets and returned.  Note 
       that no checking is done to verify if the folder actually exists.
    """
    if data_set[0] == named_location:
        try:
            return data_sets[data_set[1:]]
        except KeyError:
            raise KeyError("Named data set not found in lookup file.")

    if data_set.startswith('bak^'):
        _, backup, data_set = data_set.split('^')

        period, period_num = backup[:1], backup[1:]
        period = {'d': 'daily', 'w': 'weekly', 'm': 'monthly'}[period]
        backup = '{}.{}'.format(period, period_num)

        return os.path.join('/backups', backup, 'viseu', default_location[1:], data_set)
    else:
        if not os.path.isdir(data_set):
            return os.path.join(default_location, data_set)

    return data_set

def main():
    parser = argparse.ArgumentParser(description='Find where a named data '
        'set truly resides')
    parser.add_argument('data_set', help='The location of the data set. If '
        'names specified in a lookup file can be selected with a prefix of '
        '{0}.'.format(named_location))
    args = parser.parse_args()

    try:
        print(where(args.data_set))
    except KeyError:
        print('Named data set "{0}" not found in lookup file.'.format(args.data_set), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
