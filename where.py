#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six

import sys
import os.path
import json
import argparse

import multiworm

named_location = '%'

data_file = os.path.join(os.path.dirname(__file__), 'data_sets.json')
with open(data_file, 'r') as f:
    data_sets = json.load(f)

def where(data_set):
    if data_set[0] == named_location:
        data_set = data_sets[data_set[1:]]
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