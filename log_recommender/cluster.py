import argparse
import csv
from math import sqrt
import pickle

from sklearn import cluster
from sklearn.cluster import KMeans

from csv_io import output_to_csv


def gini_impurity(clazz, clustering_stats, word_count):
    return 1 - sum((float(x[clazz] / word_count) ** 2) if clazz in x else .0 for x in clustering_stats)


def sq_avg(gini):
    return sqrt(sum(x*x for x in gini.values()) / len(gini))


def pearson(list1, list2):

    if len(list1) != len(list2):
        raise ValueError('lists must have the same length')

    mean1 = sum(list1) / len(list1)
    mean2 = sum(list2) / len(list2)

    num = sum([(list1[i] - mean1) * (list2[i] - mean2) for i in range(len(list1))])
    denum = sqrt(sum([(list1[i] - mean1) ** 2 for i in range(len(list1))])) \
            * sqrt(sum([(list2[i] - mean2) ** 2 for i in range(len(list2))]))
    return num / denum


def run_k_means(logs_for_training, log_vectors, classes, n_clusters):

    print ("Running clustering with n cluster=", n_clusters)

    k_means = cluster.KMeans(n_clusters=n_clusters)
    k_means.fit(log_vectors)
    KMeans(algorithm='auto', copy_x=True, init='k-means++')

    clustering_stats = [{} for i in range(n_clusters)]
    word_count = dict([(clazz, 0) for clazz in classes])
    for i, log in enumerate(logs_for_training):
        cluster_dict = clustering_stats[k_means.labels_[i]]
        if log.first_word_cathegory not in cluster_dict:
            cluster_dict[log.first_word_cathegory] = 0
        cluster_dict[log.first_word_cathegory] += 1
        word_count[log.first_word_cathegory] += 1

    gini = dict([(clazz, gini_impurity(clazz, clustering_stats, word_count[clazz])) for clazz in classes])
    gini_total = sq_avg(gini)

    pearsons = [[-100 for i in range(len(classes))] for j in range(len(classes))]
    for i, clazz in enumerate(classes):
        for j, clazz1 in enumerate(classes):
            pearsons[i][j] = pearson(list(map(lambda x: x[clazz] if clazz in x else 0, clustering_stats)),
                                         list(map(lambda x: x[clazz1] if clazz1 in x else 0, clustering_stats)))

    output_to_csv(
        args.output_pearson_file,
        ['word'] + classes,
        lambda d1,d2: [d1[1]] + d2[d1[0]],
        enumerate(classes),
        pearsons
    )

    output_to_csv(args.k_means_clustering_stats_file,
        ['word'] + list(range(len(clustering_stats))) + ['total', 'gini'],
        lambda stats,classes,wc=word_count,gi=gini:
            [stats] + list(map(lambda x: x[stats] if stats in x else 0, classes)) + [wc[stats], gi[stats]],
        classes,
        clustering_stats
    )
    # Ignoring total gini for now


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--logs-from-major-classes-file', action='store', default='../major_classes_logs.pkl')
    parser.add_argument('--classes-file', action='store', default='../classes.csv')
    parser.add_argument('--binary-context-vector-file', action='store', default='../binary_context_vectors.dat')
    parser.add_argument('--output-pearson-file', action='store', default='../generated_stats/output_pearsons.csv')
    parser.add_argument('--k-means-clustering-stats-file', action='store', default='../generated_stats/k_means_clustering_stats.csv')
    args = parser.parse_args()

    with open(args.classes_file, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            classes = row

    with open(args.logs_from_major_classes_file, 'rb') as f:
        logs_from_major_classes = pickle.load(f)

    with open(args.binary_context_vector_file, 'r') as f:
        binary_context_vectors = [row.split() for row in f]

    run_k_means(logs_from_major_classes, binary_context_vectors, classes, 10)


# test data - use a separate proj for testing
# remove OTHER class
# make nn to identify the exact word
# after that stemmed word,
# do clustering to identify 'similar' first words
# group 'similar' first words and rerun classification
# table of freqs of words in context depending on freqs THRESHOLD
# table of classes depending on threshold of OTHER (presenc in proj or just freq)
# consider ++ == = alone with tokens
# same amount of test data for different classes


# plot everything.
# extract seconds words and see

# too many zeros in vectors. change the way we store them