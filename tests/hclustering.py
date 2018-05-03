from deepdiff import DeepDiff
from log_recommender.hclustering import ClusteringTree, tree_from_dendrogram

__author__ = 'hlib'

import unittest

class HClusteringTest(unittest.TestCase):
    def test_tree_from_dendrogram_trivial(self):

        dendrogram = [[0, 1]]

        expected = ClusteringTree.node(2, ClusteringTree.leaf(0), ClusteringTree.leaf(1))

        actual = tree_from_dendrogram(dendrogram)

        self.assertEqual(DeepDiff(expected, actual), {})

    def test_tree_from_dendrogram_simple(self):

        dendrogram = [[0, 1],[3, 2]]

        expected = ClusteringTree.node(4,
            ClusteringTree.node(3, ClusteringTree.leaf(0), ClusteringTree.leaf(1)),
            ClusteringTree.leaf(2)
        )

        actual = tree_from_dendrogram(dendrogram)

    def test_tree_from_dendrogram_medium(self):

        dendrogram = [[3, 4], [6, 5], [1, 2], [8, 7], [0, 9]]

        expected = ClusteringTree.node(10,
                                       ClusteringTree.leaf(0),
                                       ClusteringTree.node(9,
                                                           ClusteringTree.node(8, ClusteringTree.leaf(1), ClusteringTree.leaf(2)),
                                                           ClusteringTree.node(7,
                                                                               ClusteringTree.node(6,
                                                                                                   ClusteringTree.leaf(3),
                                                                                                   ClusteringTree.leaf(4)),
                                                                               ClusteringTree.leaf(5))))

        actual = tree_from_dendrogram(dendrogram)

        self.assertEqual(DeepDiff(expected, actual), {})

        self.assertEqual(DeepDiff(expected, actual), {})


if __name__ == '__main__':
    unittest.main()