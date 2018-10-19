import argparse
import csv
import itertools
from copy import deepcopy
from random import shuffle

import numpy
from numpy.core.multiarray import ndarray

from logrec.cluster.hclustering import get_first_words, jaccard
from logrec.util import io_utils
from logrec.util.io_utils import load_classes

__author__ = 'hlib'

from sklearn import manifold
import matplotlib.pyplot as plt
import pandas as pd

def compute_distances(flattened_data, metric):
    n_vectors = len(flattened_data)
    distances = ndarray(shape=(n_vectors, n_vectors))
    for i in range(n_vectors):
        for j in range(n_vectors):
            distances[i][j] = metric(flattened_data[i], flattened_data[j])
    return distances

def plot_data(data, annotations, cluster_names, title, dissimilarity='precomputed'):

    mds = manifold.MDS(n_components=2, metric=True, dissimilarity=dissimilarity)
    transformed_data = mds.fit_transform(data)
    transformed = pd.DataFrame(transformed_data)

    fig, ax = plt.subplots()
    start = 0

    for cluster_annotations in annotations:
        end = start + len(cluster_annotations)
        x1 = transformed[start:end][0]
        z1 = transformed[start:end][1]
        ax.scatter(x1, z1)
        for i, annot in enumerate(cluster_annotations):
            ax.annotate(annot, (x1[start + i],z1[start + i]))
        start = end

    plt.legend(cluster_names)
    plt.title(title)
    plt.show()

def matches_start_of_list(sublist, list):
    for choice in sublist:
        for w1, w2 in zip(list, choice):
            if w1 != w2:
                break
            return True
    return False


def process_filter_input(filters):
    flts = []
    for filter in filters:
        flts.append(list(map(lambda x: x.split(), filter.split('|'))))
    return flts


def get_words_bag(binary_vector, interesting_words_from_context):
    return [w for b,w in zip(binary_vector, interesting_words_from_context) if b == 1]


def get_submatrix(matrix, slice_size, slices_to_take):
    submatrix_dim = slice_size * len(slices_to_take)
    submatrix = numpy.ndarray(shape=(submatrix_dim, submatrix_dim))
    it=itertools.chain(*map(lambda s: range(s* slice_size, (s+1) * slice_size), slices_to_take))
    it1 = deepcopy(it)
    for i, ind_i in enumerate(it1):
        it2 = deepcopy(it)
        for j, ind_j in enumerate(it2):
            submatrix[i][j] = matrix[ind_i][ind_j]
    return submatrix


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--autoencode-dist-file', action='store', default='../../AutoenCODE/out/rae/corpus.dist.matrix.csv')
    parser.add_argument('--context-corpus-file', action='store', default='../../AutoenCODE/data/corpus.src')
    parser.add_argument('--n-logs-pick-for-rae-from-each-class', action='store', type=int, default=50)
    parser.add_argument('--min-word-occurencies', action='store', type=int, default=1500)
    parser.add_argument('--context-index-file', action='store', default='../context.index')
    parser.add_argument('--word-to-vec-out-file', action='store', default='../../AutoenCODE/out/word2vec/word2vec.out')
    args = parser.parse_args()



    major_classes_logs = io_utils.load_major_classes_logs()

    matrix = []
    with open(args.autoencode_dist_file, 'r') as f:
        for line in f:
            matrix.append(line.split(','))

    full_contexts = []
    csv.field_size_limit(150000)
    with open(args.context_corpus_file, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            full_contexts.append(row)

    ids = []
    with open(args.context_index_file, 'r') as f:
        for line in f:
            ids.append(line)

    matrix = numpy.array(matrix, dtype=float)
    if matrix.shape[0] != matrix.shape[1]:
        raise AssertionError("Matrix is not square!")

    classes = load_classes()

    words2vec_words = {}
    with open(args.word_to_vec_out_file, 'r') as f:
        f.readline()
        for line in f:
            split_line = line[:-1].split(' ')
            words2vec_words[split_line[0]] = list(map(lambda x: float(x), split_line[1:1+5]))

    # words2vec_contexts = []
    # for context in full_contexts:
    #     if '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~' in context:
    #         continue
    #     context_vector = sum_vectors(list(map(lambda w, ww=words2vec_words: ww[w], context)))
    #     words2vec_contexts.append(context_vector)
    #
    # selected_words2vec_contexts = []
    # selected_words2vec_contexts.append(words2vec_contexts[0])
    # selected_words2vec_contexts.append(words2vec_contexts[1])
    # selected_words2vec_contexts.append(words2vec_contexts[2])
    # selected_words2vec_contexts.append(words2vec_contexts[2000])
    # selected_words2vec_contexts.append(words2vec_contexts[2001])
    # selected_words2vec_contexts.append(words2vec_contexts[2002])
    #
    # selected_full_contexts = []
    # selected_full_contexts.append([full_contexts[0], full_contexts[1], full_contexts[2]])
    # selected_full_contexts.append([full_contexts[2000], full_contexts[2001], full_contexts[2002]])
    #
    # plot_data(selected_words2vec_contexts,
    #       selected_full_contexts,
    #       "", "vord2vec contexts", dissimilarity='euclidean')
    #
    #
    # classes_word2vecs = list(filter(lambda x: x[0] in classes, words2vec_words.items()))
    #
    # plot_data([x[1] for x in classes_word2vecs],
    #           [[x[0] for x in classes_word2vecs]],
    #           "", "classes words", dissimilarity='euclidean')

    classes_to_show = [
        # 'successfully',
        'error',
        'exception',
        # 'created'
    ]
    n = args.n_logs_pick_for_rae_from_each_class
    c=args.min_word_occurencies
    submatrix = get_submatrix(matrix, n, list(map(lambda c: classes.index(c), classes_to_show)))

    # plot_data(submatrix,
    #           [[" " for i in range(classes.index(cl) * c,classes.index(cl) * c + n)]
    #                     for cl in classes_to_show],
    #           classes_to_show,
    #           title='word2vec'
    #           )
    #
    # plot_data(submatrix,
    #           [["[" + ids[i][:-1] + "]" + " ".join(full_contexts[i]) for i in range(classes.index(cl) * c,classes.index(cl) * c + n)]
    #                     for cl in classes_to_show],
    #           classes_to_show,
    #           title='word2vec with annotations'
    #           )


    data = {}
    first_words = get_first_words(major_classes_logs, 2)
    annotations = []
    # ['start', 'creating', "can't", 'exception', 'received', 'invalid', 'using', 'unexpected', 'caught', 'unable', 'not', 'removing', 'no', 'cannot', 'node', 'updating', 'started', 'executing', 'could', 'starting', 'sending', 'adding', 'created', 'setting', 'ignoring', 'waiting', 'error']
    filters = [
        # "exception",
        #        "error",
        #        "successfully",
               "created",
               # "found",
               "exception",
               # "waiting"
               ]
    filters_split = process_filter_input(filters)

    interesting_words_from_context = io_utils.load_interesting_words()
    binary_context_vectors = io_utils.load_binary_context_vectors()

    for i, line in enumerate(binary_context_vectors):
        for flt in filters_split:
            if matches_start_of_list(flt, first_words[i]):
                # split = line.split()
                # log_id = split[0]
                values = list(map(lambda x: int(x), line))
                data_map_key = "|".join(map(lambda x: " ".join(x), flt))
                if data_map_key not in data:
                    data[data_map_key] = []
                # data[data_map_key].append({'id': log_id, 'values': values})
                data[data_map_key].append({'values': values})
    for d in data.values():
        shuffle(d)
    how_many = 200

    flattened_data = [dict['values'] for i in data.items() for dict in i[1][:how_many]]
    dissimilarities_matrix = compute_distances(flattened_data, jaccard)

    plot_data(dissimilarities_matrix,
               [["" for entry in cluster[1][:how_many]] for cluster in data.items()],
               [i[0] for i in data.items()],
              title='jaccard')

    plot_data(dissimilarities_matrix,
               [[" ".join(get_words_bag(entry['values'], interesting_words_from_context))
                 # + " " + entry['id']
                        for entry in cluster[1][:how_many]] for cluster in data.items()],
               [i[0] for i in data.items()],
              title='jaccard with annotations')