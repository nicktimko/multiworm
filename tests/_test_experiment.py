from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import os.path
import unittest
import random

def fake_data(path, basename=None, frames=5000, seed=0):
    if basename is None:
        basename = 'generated_test_data'
    random.seed(seed)
    starting_blobs = random.randint(5,10)

    frames = range(1, frames+1)
    frame_period = 0.065
    t = 0.002

    new_blobs = set(random.sample(list(range(400)), starting_blobs))
    active_blobs = set()
    lost_blobs = set()
    summary = []
    for frame in frames:
        # frame and time
        line = '{0:d} {1:.3f}'.format(frame, t)
        line += '  {0:d} {1:d} {2:.1f}'.format(random.randint(10,30), random.randint(10,30), 3*random.random())
        for _ in range(5):
            # numbers...dunno what they do.
            line += '  {0:.2f} {1:.3f}'.format(10*random.random(), 2*random.random())

        for _ in range(3):
            if random.random() < 0.01:
                new_blobs.add(random.randint(500, 80000))
            if random.random() < 0.01:
                if active_blobs:
                    lost_blobs.add(random.sample(active_blobs, 1)[0])

        if new_blobs or lost_blobs:
            line += r'  %%'
            for nb in new_blobs:
                line += ' 0 {0:d}'.format(nb)
                active_blobs.add(nb)
            for lb in lost_blobs:
                line += ' {0:d} 0'.format(lb)
                active_blobs.remove(lb)
            new_blobs = set()
            lost_blobs = set()

        t += frame_period
        summary.append(line)

    return summary

class FakeExperiment(object):
    def __init__(self, seed=0, nblobs=50, frames=5000, blob_age_dist=(0,5000)):
        random.seed(seed)

        id_range = 1, 100000

        self.blob_starts = [random.randint(*blob_age_dist) for _ in range(nblobs)]
        self.blob_ends
        # make sure the extremes are in there.


class TestBlobReading(unittest.TestCase):

    def setUp(self):
        self.good_data_path = fake_data('good_data')

    def test_parse_record(self):
        data = ['']

if __name__ == '__main__':
    #unittest.main()
    print('\n'.join(fake_data('test', frames=100)))
