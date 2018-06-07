from log_recommender.util import sum_vectors

__author__ = 'hlib'

import unittest

class VisualTest(unittest.TestCase):
    def test_sum_vectors(self):
        vectors = [[0.0, 1.0, 9.0, 8.0, 7.0],
                [0.0, 1.0, 9.0, 8.0, 7.0],
                [0.0, 1.0, -9.0, 8.0, 7.0]]

        expected = [0.0, 3.0, 9.0, 24.0, 21.0]

        actual = sum_vectors(vectors)

        self.assertEqual(expected, actual)
