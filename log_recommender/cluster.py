import argparse
from math import sqrt
import pickle
from random import shuffle

from sklearn import cluster
from sklearn.cluster import KMeans

from log_recommender.csv_io import output_to_csv
from first_word_picker import get_interesting_words_from_current_log_context, get_interesting_words_from_context, \
    select_logs_for_training_and_testing, get_classes_list
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
        'generated_stats/output_pearsons.csv',
        ['word'] + classes,
        lambda d1,d2: [d1[1]] + d2[d1[0]],
        enumerate(classes),
        pearsons
    )

    output_to_csv('generated_stats/k_means_clustering_stats.csv',
        ['word'] + list(range(len(clustering_stats))) + ['total', 'gini'],
        lambda stats,classes,wc=word_count,gi=gini:
            [stats] + list(map(lambda x: x[stats] if stats in x else 0, classes)) + [wc[stats], gi[stats]],
        classes,
        clustering_stats
    )
    # Ignoring total gini for now



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-word-occurencies', action='store', type=int, default=20)
    parser.add_argument('--log-contexts-for-training-file', action='store', default='generated_stats/log_contexts_for_training.csv')
    parser.add_argument('--args-logs-for-training-file', action='store', default='logs_for_training.pkl')
    args = parser.parse_args()

    with open('pplogs.pkl', 'rb') as i:
        preprocessed_logs = pickle.load(i)
    classes = get_classes_list(preprocessed_logs, args.min_word_occurencies)
    interesting_words_from_context = get_interesting_words_from_context(preprocessed_logs)
    preprocessed_logs = classify_logs_by_first_word(preprocessed_logs, classes)
    logs_for_training, logs_for_testing = select_logs_for_training_and_testing(preprocessed_logs, classes, args.min_word_occurencies)
    shuffle(logs_for_training)
    logs_for_training = logs_for_training[::15]

    logs_for_training.sort(key=lambda x: x.first_word_cathegory)

    # log_vectors = [build_vector(get_interesting_words_from_current_log_context(log, interesting_words_from_context),
    #                             interesting_words_from_context) for log in logs_for_training]
    #run_k_means(logs_for_training, log_vectors, classes, 10)

    logs_for_training_without_empty_contexts = []
    log_context_vector = []
    for log in logs_for_training:
        log_context = get_interesting_words_from_current_log_context(log, interesting_words_from_context)
        if len(log_context) > 0:
            log_context_vector.append(log_context)
            logs_for_training_without_empty_contexts.append(log)
    with open(args.log_contexts_for_training_file, 'w') as f:
        for log_vector in log_context_vector:
            f.write(" ".join(log_vector) + "\n")
    with open(args.args_logs_for_training_file, "wb") as f:
        pickle.dump(logs_for_training_without_empty_contexts, f)


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

