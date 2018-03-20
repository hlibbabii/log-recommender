import operator
from sortedcontainers import SortedList
from util import without_duplicates

__author__ = 'hlib'


def get_most_suitable_log_statements(corpus, idfs, current_context, how_many):
    print("Looking for the most suitable log statement for context: " + str(current_context))
    scores = SortedList(key=operator.itemgetter(1))
    for l in corpus:
        score = get_score(l.context_words, current_context, idfs)
        scores.add((l, score))
    return reversed(scores[-how_many:])


def get_score(context, current_context, idfs):
    current_score = 0.0
    for word1 in without_duplicates(context):
        for word2 in without_duplicates(current_context):
            if word1 == word2:
                current_score += idfs.get(word1)
    return current_score


def test_pick_log(preprocessed_logs, idfs):
    print("\n===============Testing=====================\n")
    log_entry_for_testing = preprocessed_logs[5700]
    most_suitable_log_statements = get_most_suitable_log_statements(preprocessed_logs, idfs, log_entry_for_testing.context_words, 10)
    for log_entry, score in most_suitable_log_statements:
        print(str(log_entry.log_text))
        print(str(log_entry.context))
        print(str(score) + "\n")

    print("Real log statement: " + str(log_entry_for_testing.log_text))
    print("Current context: " + str(log_entry_for_testing.context))
