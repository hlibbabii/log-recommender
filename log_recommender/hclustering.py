import argparse
import logging
import pickle
from pprint import pprint
from numpy import genfromtxt


def run_hierarchical_clustering(log_vectors, first_words_vector, contexts):
    import fastcluster

    linkage = fastcluster.linkage(log_vectors, method='single', metric=lambda x, y: dist_matrix[x, y])
    for i, linkage_row in enumerate(linkage):
        f1 = ""
        node_index1 = linkage_row[0].astype(int)
        if node_index1 < len(first_words_vector):
            f1 = " ".join(first_words_vector[node_index1])
        f2 = ""
        node_index2 = linkage_row[1].astype(int)
        if node_index2 < len(first_words_vector):
            f2 = " ".join(first_words_vector[node_index2])
        print(i)
        print(str(node_index1) + " " + str(node_index2) + " " +str(linkage_row[2]) + " " + str(linkage_row[3].astype(int)) +
              " " + f1 + " + " + f2)
        print("===")
        if node_index1 < len(first_words_vector):
            print(contexts[node_index1])
        print("===")
        if node_index2 < len(first_words_vector):
            print(contexts[node_index2])

    # The output of linkage is stepwise dendrogram, which is represented as an (N − 1) ×
    # 4 NumPy array with floating point entries (dtype=numpy.double). The first two
    # columns contain the node indices which are joined in each step. The input nodes are
    # labeled 0, . . . , N − 1, and the newly generated nodes have the labels N, . . . , 2N − 2.
    # The third column contains the distance between the two nodes at each step, ie. the
    # current minimal distance at the time of the merge. The fourth column counts the
    # number of points which comprise each new node.


def get_first_words(preprocessed_logs, how_many_words):
    return list(map(lambda x: x.text_words[:how_many_words], preprocessed_logs))


def get_contexts(preprocessed_logs):
    return list(map(lambda x: x.context_before, preprocessed_logs))


class ClusteringTree(object):
    def __init__(self, payload, left_tree, right_tree):
        self.payload = payload
        self.left_tree = left_tree
        self.right_tree = right_tree

    @classmethod
    def leaf(cls, payload):
        return cls(payload, None, None)

    @classmethod
    def node(cls, payload, left_tree, right_tree):
        return cls(payload, left_tree, right_tree)


def tree_from_dendrogram(dendrogram):
    n_leaves = len(dendrogram) + 1
    created_trees = []
    for ind, entry in enumerate(dendrogram):
        left_tree = ClusteringTree.leaf(entry[0]) if entry[0] < n_leaves else created_trees[entry[0] - n_leaves]
        right_tree = ClusteringTree.leaf(entry[1]) if entry[1] < n_leaves else created_trees[entry[1] - n_leaves]
        created_trees.append(ClusteringTree.node(n_leaves + ind, left_tree, right_tree))
    return created_trees[-1]



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--autoencode-dist-file', action='store', default='../AutoenCODE/out/rae/corpus.dist.matrix.csv')
    parser.add_argument('--input-preprocessed-logfile', action='store', default='logs_for_training.pkl')
    args = parser.parse_args()

    dist_matrix = genfromtxt(args.autoencode_dist_file, delimiter=',')

    with open(args.input_preprocessed_logfile, 'rb') as i:
        preprocessed_logs = pickle.load(i)
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Number of pplogs: " + str(len(preprocessed_logs)))

    first_words = get_first_words(preprocessed_logs, 2)
    contexts = get_contexts(preprocessed_logs)

    run_hierarchical_clustering([[i] for i in range(dist_matrix.shape[0])], first_words, contexts)