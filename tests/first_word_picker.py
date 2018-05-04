from deepdiff import DeepDiff
from log_recommender.first_word_picker import build_vector
from log_recommender.hclustering import ClusteringTree, tree_from_dendrogram, break_into_multiple_trees_by_wfs

__author__ = 'hlib'

import unittest

class HClusteringTest(unittest.TestCase):
    def test_build_vector(self):
        found_words = ["a", "b", "c", "e"]
        interesting_words = ["a", "c", "d"]

        expected = [1, 1, 0]
        actual = build_vector(found_words, interesting_words)

        self.assertEqual(expected, actual)



if __name__ == '__main__':
    unittest.main()