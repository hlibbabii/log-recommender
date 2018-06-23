import argparse
import logging
from numpy import genfromtxt
from util import io_utils


def run_hierarchical_clustering(log_vectors, first_words_vector, contexts, metric_function):
    import fastcluster

    linkage = fastcluster.linkage(log_vectors, method='complete', metric=metric_function)
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
    clusters = break_into_multiple_trees_by_wfs(tree_from_dendrogram(linkage[:, [0, 1]].astype(int)), 50)
    list_of_payload_lists = list(map(lambda cl: cl.get_all_leaf_payloads(), clusters))
    print("Cluster sizes are:")
    print(list(map(lambda l: len(l), list_of_payload_lists)))
    for list_of_payloads in list_of_payload_lists:
        print("===============")
        print(list(map(lambda p: first_words_vector[p], list_of_payloads)))

    # The output of linkage is stepwise dendrogram, which is represented as an (N − 1) ×
    # 4 NumPy array with floating point entries (dtype=numpy.double). The first two
    # columns contain the node indices which are joined in each step. The input nodes are
    # labeled 0, . . . , N − 1, and the newly generated nodes have the labels N, . . . , 2N − 2.
    # The third column contains the distance between the two nodes at each step, ie. the
    # current minimal distance at the time of the merge. The fourth column counts the
    # number of points which comprise each new node.


def get_first_words(preprocessed_logs, how_many_words):
    return list(map(lambda x: x.get_first_words(how_many_words), preprocessed_logs))


def get_contexts(preprocessed_logs):
    return list(map(lambda x: x.context.context_before, preprocessed_logs))


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

    def is_leaf(self):
        return self.left_tree is None

    def get_all_leaf_payloads(self):
        if self.is_leaf():
            return [self.payload]
        else:
            return self.left_tree.get_all_leaf_payloads() + self.right_tree.get_all_leaf_payloads()


def tree_from_dendrogram(dendrogram):
    n_leaves = len(dendrogram) + 1
    created_trees = []
    for ind, entry in enumerate(dendrogram):
        left_tree = ClusteringTree.leaf(entry[0]) if entry[0] < n_leaves else created_trees[entry[0] - n_leaves]
        right_tree = ClusteringTree.leaf(entry[1]) if entry[1] < n_leaves else created_trees[entry[1] - n_leaves]
        created_trees.append(ClusteringTree.node(n_leaves + ind, left_tree, right_tree))
    return created_trees[-1]


def break_into_multiple_trees_by_wfs(tree, how_many):
    trees = [tree]
    while how_many > 1:
        how_many -= 1
        current_tree = trees.pop(0)
        while current_tree.is_leaf():
            #TODO check if there is non-leaf tree
            trees.append(current_tree)
            current_tree = trees.pop(0)
        trees.extend([current_tree.left_tree, current_tree.right_tree])
    return trees

def jaccard(vector1, vector2):
    num = 0
    denum = 0
    for x, y in zip(vector1, vector2):
        if x or y:
            denum += 1
            if x and y:
                num +=1
    return (1 - num / denum) if denum != 0 else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--autoencode-dist-file', action='store', default='../../AutoenCODE/out/rae/corpus.dist.matrix.csv')
    parser.add_argument('--distance-metric', action='store', default='jaccard')
    parser.add_argument('--binary-context-vector-file', action='store', default='../ ')
    args = parser.parse_args()

    if args.distance_metric == 'word2vec':
        dist_matrix = genfromtxt(args.autoencode_dist_file, delimiter=',')
        metric_function = lambda x, y, m=dist_matrix: m[x, y]
        vector = [[i] for i in range(dist_matrix.shape[0])]
    elif args.distance_metric == 'jaccard':
        metric_function = jaccard
        vector = io_utils.load_binary_context_vectors()[:1000]
    else:
        raise ValueError("Invalid metric name: " + args.distance_metric)

    major_classes_logs = io_utils.load_major_classes_logs()
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Number of pplogs: " + str(len(major_classes_logs)))

    first_words = get_first_words(major_classes_logs, 2)
    contexts = get_contexts(major_classes_logs)

    run_hierarchical_clustering(vector, first_words, contexts, metric_function)