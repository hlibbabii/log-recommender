import argparse
import itertools
import logging
import operator
from collections import Counter

from logrec.legacy.classify_and_select_major_logs import get_top_projects_by_log_number
from logrec.util import io_utils

__author__ = 'hlib'

def get_word_frequences(logs, words_from_log_func):
    dict = {}
    for key, group in itertools.groupby(logs, key=lambda x: x.project):
        dict[key] = Counter(itertools.chain.from_iterable(map(words_from_log_func, group)))
    return dict

def calc_frequency_stats(occurences):
    project_sums = {}
    for project_name, project_occurences in occurences.items():
        project_sums[project_name] = sum(project_occurences.values())
    total_sum = sum(project_sums.values())
    frequencies = {}
    all_occurences = {}
    for project_name, project_occurences in occurences.items():
        for word, word_occurences in project_occurences.items():
            if word not in frequencies:
                frequencies[word] = {}
            frequencies[word][project_name] = float(word_occurences) / project_sums[project_name]
            if word in all_occurences:
                all_occurences[word] += word_occurences
            else:
                all_occurences[word] = word_occurences
    n_projects = len(occurences)
    for word in frequencies:
        frequencies[word]['__median__'] = median(
            sorted(frequencies[word].items(), key=operator.itemgetter(1), reverse=True),
            n_projects
        )
    for word in frequencies:
        frequencies[word]['__all__'] = float(all_occurences[word]) / total_sum
        frequencies[word]['__all_abs__'] = all_occurences[word]
        frequencies[word]['__found_in_projects__'] = len(frequencies[word]) - 3
    return frequencies

def avg(sorted_list, full_list_length):
    if full_list_length // 2 >= len(sorted_list):
        first = 0.0
    else:
        first = sorted_list[full_list_length // 2][1]
    if full_list_length // 2 > len(sorted_list):
        second = 0.0
    else:
        second = sorted_list[full_list_length // 2 - 1][1]
    return (first + second) / 2


def central(sorted_list, full_list_length):
    if full_list_length // 2 >= len(sorted_list):
        return 0.0
    return sorted_list[full_list_length // 2][1]

def median(sorted_list, full_list_length):
    func = avg if full_list_length % 2 == 0 else central
    return func(sorted_list, full_list_length)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--min-log-number-per-project', action='store', type=int, default=100)
    parser.add_argument('--context-lines-to-consider', action='store', type=int, default=4)
    args = parser.parse_args()

    preprocessed_logs_gen = io_utils.load_preprocessed_logs()

    logging.info("Loading project stats...")
    project_stats = io_utils.load_project_stats()
    top_projects = get_top_projects_by_log_number(project_stats, args.min_log_number_per_project)

    logging.info("Calculating word frequencies...")
    frequencies = get_word_frequences(preprocessed_logs_gen, lambda x: x.text_words)
    freq_stats = calc_frequency_stats(frequencies)

    io_utils.dump_frequencies_stats(freq_stats, top_projects)
    io_utils.dump_frequencies_stats_binary(freq_stats)

    first_word_frequencies = get_word_frequences(preprocessed_logs_gen, lambda x: [x.get_first_word()])
    first_word_freq_stats = calc_frequency_stats(first_word_frequencies)
    io_utils.dump_first_word_frequencies_stats(first_word_freq_stats, top_projects)
    io_utils.dump_first_word_frequencies_stats_binary(first_word_freq_stats)

    context_word_frequencies = get_word_frequences(preprocessed_logs_gen,
                                                   lambda x, n=args.context_lines_to_consider: x.get_context_words(n))
    context_word_freq_stats = calc_frequency_stats(context_word_frequencies)
    io_utils.dump_context_frequencies_stats_binary(context_word_freq_stats)
