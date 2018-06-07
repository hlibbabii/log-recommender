import argparse
import operator
import pickle
from math import log
from random import randint

from sortedcontainers import SortedList
import io_utils

from util import without_duplicates


__author__ = 'hlib'


def get_most_suitable_log_statements(corpus, idfs, current_context, how_many, lines_to_consider):
    print("Looking for the most suitable log statement for context: " + str(current_context))
    scores = SortedList(key=operator.itemgetter(1))
    for l in corpus:
        score = get_score(l.get_context_words(lines_to_consider), current_context, idfs)
        scores.add((l, score))
    return reversed(scores[-how_many:])


def get_score(context1, context2, idfs):
    common_score = 0.0
    context1_nodup = without_duplicates(context1)
    context2_nodup = without_duplicates(context2)
    for word1 in context1_nodup:
        for word2 in context2_nodup:
            if word1 == word2:
                common_score += idfs.get(word1)
                break
    all_score = 0.0
    for word1 in context1_nodup:
        all_score += idfs.get(word1)
    for word1 in context2_nodup:
        all_score += idfs.get(word1)
    return common_score / (all_score - common_score)


def get_idfs(context_list):
    sum = dict()
    vector_number = float(len(context_list))
    for l in context_list:
        for context_string in l:
            if context_string in sum:
                sum[context_string] += 1
            else:
                sum[context_string] = 1
    idfs = {key: log(vector_number / value, 2) for key, value in sum.items()}
    return sorted(idfs.items(), key=operator.itemgetter(1), reverse=True), idfs


def test_pick_log(preprocessed_logs, idfs, log_to_test, context_lines_to_consider):
    print("\n===============Testing=====================\n")
    most_suitable_log_statements = get_most_suitable_log_statements(preprocessed_logs, idfs,
                                                                    log_to_test.get_context_words(context_lines_to_consider),
                                                                    10, context_lines_to_consider)
    for log_entry, score in most_suitable_log_statements:
        print("--------------------------------------\n")
        print(str(log_entry.text))
        print(str(log_entry.context.context_before))
        print(str(score) + "\n")
        print("--------------------------------------\n")


    print("Real log statement: " + str(log_to_test.text))
    print("Current context: " + str(log_to_test.context.context_before))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--context-lines-to-consider', action='store', type=int, default=4)
    args = parser.parse_args()

    preprocessed_logs = io_utils.load_preprocessed_logs()
    sorted_idf_tuples, idfs = get_idfs(list(map(lambda l: l.get_context_words(args.context_words_to_consider),
                                                preprocessed_logs)))
    rand_num = randint(0, len(preprocessed_logs) - 1)
    log_to_test = preprocessed_logs[rand_num]
    test_pick_log(preprocessed_logs, idfs, preprocessed_logs[rand_num], args.context_lines_to_consider)