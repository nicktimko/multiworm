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
    if data_set[0] == named_location:
        return data_sets[data_set[1:]]

    if data_set.startswith('back^'):
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