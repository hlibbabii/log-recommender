#!/usr/bin/env python

import argparse
import logging
from operator import attrgetter
from random import shuffle

from logrec.util import io

__author__ = 'hlib'


def get_top_projects_by_log_number(project_stats, log_number_threshold):
    return list(map(lambda x : x[0],
              sorted(filter(lambda x: x[1] >= log_number_threshold, project_stats.items()), key=lambda x: x[1], reverse=True)
              ))


def get_most_freq_first_words(first_word_freq_stats):
    return list(map(lambda x:x[0], filter(lambda x:x[1]['__median__'], first_word_freq_stats.items())))

def classify_logs_by_first_word(preprocessed_logs, significant_words):
    for log in preprocessed_logs:
        first_word = log.get_first_word()
        log.first_word_cathegory = first_word if first_word in significant_words else "OTHER__"
    return preprocessed_logs


def select_logs_from_major_classes(preprocessed_logs, attr_getter, classes, how_many_of_each):
    shuffle(preprocessed_logs)
    major_classes_logs = []
    other_logs = []
    d = dict([(cl, 0) for cl in classes])
    for log in preprocessed_logs:
        if attr_getter(log) in classes and d[attr_getter(log)] < how_many_of_each:
            major_classes_logs.append(log)
            d[attr_getter(log)] += 1
        else:
            other_logs.append(log)
    shuffle(major_classes_logs)
    return major_classes_logs, other_logs


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--context-lines-to-consider', action='store', type=int, default=4)
    parser.add_argument('--min-word-occurencies', action='store', type=int, default=700)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    preprocessed_logs = io.load_preprocessed_logs()
    classes = io.load_classes()

    classified_logs = classify_logs_by_first_word(preprocessed_logs, classes)
    logs_from_major_classes, other_logs = select_logs_from_major_classes(classified_logs, attrgetter('first_word_cathegory'),
                                                                         classes, args.min_word_occurencies)

    io.dump_classified_logs(classified_logs)
    io.dump_major_classes_logs(logs_from_major_classes)
