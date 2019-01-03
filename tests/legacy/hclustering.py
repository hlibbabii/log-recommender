from logrec.legacy.cluster.hclustering import ClusteringTree, tree_from_dendrogram, break_into_multiple_trees_by_wfs, \
    jaccard

__author__ = 'hlib'

import unittest

class HClusteringTest(unittest.TestCase):
    def test_tree_from_dendrogram_trivial(self):

        dendrogram = [[0, 1]]

        expected = ClusteringTree.node(2, ClusteringTree.leaf(0), ClusteringTree.leaf(1))

        actual = tree_from_dendrogram(dendrogram)

        self.assertEqual(expected, actual)

    def test_tree_from_dendrogram_simple(self):

        dendrogram = [[0, 1],[3, 2]]

        expected = ClusteringTree.node(4,
            ClusteringTree.node(3, ClusteringTree.leaf(0), ClusteringTree.leaf(1)),
            ClusteringTree.leaf(2)
        )

        actual = tree_from_dendrogram(dendrogram)

        self.assertEqual(expected, actual)

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

        self.assertEqual(expected, actual)

    def test_break_into_multiple_trees_by_wfs_trivial(self):
        tree = ClusteringTree.node(10,
                                       ClusteringTree.leaf(0),
                                       ClusteringTree.node(9,
                                                           ClusteringTree.node(8, ClusteringTree.leaf(1), ClusteringTree.leaf(2)),
                                                           ClusteringTree.node(7,
                                                                               ClusteringTree.node(6,
                                                                                                   ClusteringTree.leaf(3),
                                                                                                   ClusteringTree.leaf(4)),
                                                                               ClusteringTree.leaf(5))))
        expected = [tree]

        actual = break_into_multiple_trees_by_wfs(tree, 1)

        self.assertEqual(expected, actual)

    def test_break_into_multiple_trees_by_wfs_simple(self):
        tree = ClusteringTree.node(10,
                                       ClusteringTree.leaf(0),
                                       ClusteringTree.node(9,
                                                           ClusteringTree.node(8, ClusteringTree.leaf(1), ClusteringTree.leaf(2)),
                                                           ClusteringTree.node(7,
                                                                               ClusteringTree.node(6,
                                                                                                   ClusteringTree.leaf(3),
                                                                                                   ClusteringTree.leaf(4)),
                                                                               ClusteringTree.leaf(5))))

        expected = [ClusteringTree.leaf(0), ClusteringTree.node(9,
                                                           ClusteringTree.node(8, ClusteringTree.leaf(1), ClusteringTree.leaf(2)),
                                                           ClusteringTree.node(7,
                                                                               ClusteringTree.node(6,
                                                                                                   ClusteringTree.leaf(3),
                                                                                                   ClusteringTree.leaf(4)),
                                                                               ClusteringTree.leaf(5)))]

        actual = break_into_multiple_trees_by_wfs(tree, 2)

        self.assertEqual(expected, actual)

    def test_break_into_multiple_trees_by_wfs_equal(self):
        tree = ClusteringTree.node(14,
                                       ClusteringTree.node(12,
                                                            ClusteringTree.node(8,
                                                                               ClusteringTree.leaf(0),
                                                                               ClusteringTree.leaf(1)),
                                                            ClusteringTree.node(9,
                                                                               ClusteringTree.leaf(2),
                                                                               ClusteringTree.leaf(3))),

                                       ClusteringTree.node(13,
                                                            ClusteringTree.node(10,
                                                                               ClusteringTree.leaf(4),
                                                                               ClusteringTree.leaf(5)),
                                                            ClusteringTree.node(11,
                                                                               ClusteringTree.leaf(6),
                                                                               ClusteringTree.leaf(7))))

        expected = [ClusteringTree.node(8, ClusteringTree.leaf(0), ClusteringTree.leaf(1)),
                    ClusteringTree.node(9, ClusteringTree.leaf(2), ClusteringTree.leaf(3)),
                    ClusteringTree.node(10, ClusteringTree.leaf(4), ClusteringTree.leaf(5)),
                    ClusteringTree.node(11, ClusteringTree.leaf(6), ClusteringTree.leaf(7))]

        actual = break_into_multiple_trees_by_wfs(tree, 4)

        self.assertEqual(expected, actual)

    def test_get_all_leaf_payloads(self):
        tree = ClusteringTree.node(10,
                               ClusteringTree.leaf(0),
                               ClusteringTree.node(9,
                                                   ClusteringTree.node(8, ClusteringTree.leaf(1), ClusteringTree.leaf(2)),
                                                   ClusteringTree.node(7,
                                                                       ClusteringTree.node(6,
                                                                                           ClusteringTree.leaf(3),
                                                                                           ClusteringTree.leaf(4)),
                                                                       ClusteringTree.leaf(5))))
        expected = [0, 1, 2, 3, 4, 5]

        actual = tree.get_all_leaf_payloads()

        self.assertEqual(expected, actual)

    def test_jaccard_simple(self):
        v1 = [0, 0, 1, 1, 1]
        v2 = [1, 0, 1, 0, 0]

        self.assertEqual(0.75, jaccard(v1, v2))

if __name__ == '__main__':
    unittest.main()