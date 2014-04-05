from __future__ import (
        absolute_import, division, print_function, unicode_literals)
import six
from six.moves import (zip, filter, map, reduce, input, range)

import unittest

from tapeworm.tape import join_segments

def setify(subgraphs):
    return set(tuple(sg) for sg in subgraphs)

class TestJoining(unittest.TestCase):
    def setUp(self):
        pass

    def test_basic(self):
        edges = [(1, 2), (2, 3), (4, 5), (6, 7)]
        expected_output = [[1, 2, 3], [4, 5], [6, 7]]
        self.assertEqual(
                setify(join_segments(edges)),
                setify(expected_output)
            )

    def test_reject_merge(self):
        edges = [(1, 3), (2, 3), (3, 4)]
        try:
            join_segments(edges)
        except ValueError:
            pass # expected
        except:
            self.fail("Splitting edges raised unexpected error")
        else:
            self.fail("Function did not reject merging digraph edges")

    def test_reject_fork(self):
        edges = [(1, 2), (2, 3), (2, 4)]

        try:
            join_segments(edges)
        except ValueError:
            pass # expected
        except:
            self.fail("Forking edges raised unexpected error")
        else:
            self.fail("Function did not raise error on forking digraph edges")

    def test_unmatched_nodes(self):
        edges = [(1, 2), (2, 3), (4, 5)]
        nodes1 = set(range(1, 6))
        nodes2 = set(range(1, 8))

        segments, unmatched1 = join_segments(edges, nodes1)
        segments, unmatched2 = join_segments(edges, nodes2)

        self.assertEqual(unmatched1, set())
        self.assertEqual(unmatched2, set([6, 7]))

    def test_reject_missing_node(self):
        edges = [(1, 2), (2, 3), (4, 50)]
        nodes = set(range(1, 5))

        try:
            join_segments(edges, nodes)
        except ValueError:
            pass # expected
        except:
            self.fail("Edge node missing from nodes raised unexpected error")
        else:
            self.fail("Function did not raise error when edge node was absent from nodes")

    def test_build_backwards(self):
        edges = [(2, 3), (1, 2)]
        expected_output = [[1, 2, 3]]

        self.assertEqual(
                setify(join_segments(edges)),
                setify(expected_output)
            )

    def test_build_backwards_with_nodes(self):
        edges = [(3, 4), (2, 3), (1, 2)]
        nodes = set(range(1, 5))
        expected_output = [[1, 2, 3, 4]]

        segments, unmatched = join_segments(edges, nodes)
        self.assertEqual(
                setify(segments),
                setify(expected_output)
            )

    def test_join_existing_subgraphs(self):
        """
        Check that traces that should be connected aren't chunked into subgraphs.

        Previously, we didn't and several data sets hit this bug, e.g. 
        20130413_133837, 
        """
        edges = [(3, 4), (1, 2), (2, 3)]
        expected_output = [[1, 2, 3, 4]]

        segments = join_segments(edges)
        self.assertEqual(
               setify(segments),
               setify(expected_output)
           )

        edges = [(1, 2), (3, 4), (2, 3)]

        segments = join_segments(edges)
        self.assertEqual(
                setify(segments),
                setify(expected_output)
            )
