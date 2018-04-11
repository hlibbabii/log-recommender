from math import sqrt
import pickle
from functools import reduce
from pprint import pprint
from sklearn import cluster
from sklearn.cluster import KMeans
from csv_io import output_clustering_stats, output_pearsons
from first_word_picker import get_interesting_words_from_logs, build_vector, get_interesting_words_from_context, \
    select_logs_for_nn, get_classes_list, MIN_OCCURRENCES
from freqs import classify_logs_by_first_word


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


if __name__ == "__main__":
    with open('pplogs.pkl', 'rb') as i:
        preprocessed_logs = pickle.load(i)
    classes = get_classes_list(preprocessed_logs)
    interesting_words_from_context = get_interesting_words_from_context(preprocessed_logs)
    preprocessed_logs = classify_logs_by_first_word(preprocessed_logs, classes)
    logs_for_nn, demo_logs = select_logs_for_nn(preprocessed_logs, classes, MIN_OCCURRENCES)

    logs_for_nn.sort(key=lambda x: x.first_word_cathegory)
    print(list(map(lambda x: x.first_word_cathegory, logs_for_nn[::300])))

    log_vectors = [build_vector(get_interesting_words_from_logs(log, interesting_words_from_context),
                                interesting_words_from_context) for log in logs_for_nn]

    N_CLUSTERS = 10

    print ("Running clustering with n cluster=", N_CLUSTERS)

    k_means = cluster.KMeans(n_clusters=N_CLUSTERS)
    k_means.fit(log_vectors)
    KMeans(algorithm='auto', copy_x=True, init='k-means++')

    clustering_stats = [{} for i in range(N_CLUSTERS)]
    word_count = dict([(clazz, 0) for clazz in classes])
    for i, log in enumerate(logs_for_nn):
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

    output_pearsons('generated_stats/output_pearsons.csv', pearsons, classes)

    for p in pearsons:
        print(p)

    output_clustering_stats('generated_stats/clustering_stats.csv',
                            clustering_stats, word_count, gini, gini_total,
                            classes)



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


# hierarchical clustering.
# plot everything.
# extract seconds words and see

