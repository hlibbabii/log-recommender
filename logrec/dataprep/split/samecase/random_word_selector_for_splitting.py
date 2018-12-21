import logging
import math
import os
import random
import re
from collections import defaultdict

from logrec.dataprep import base_project_dir

logger = logging.getLogger(__name__)

base_dataset_dir = f'{base_project_dir}/nn-data/devanbu_no_replaced_identifier_split_no_tabs_new_splits3_under_5000_15_percent/'
path_to_labeled_data = os.path.join(base_dataset_dir, 'sample.txt')
path_to_labeled_data2 = os.path.join(base_dataset_dir, 'sample2.txt')
vocab_file = os.path.join(base_dataset_dir, 'vocab.txt')


def get_already_selected_words():
    selected_words = defaultdict(list)
    key_to_labeled_data = {}
    with open(path_to_labeled_data, 'r') as f:
        for line in f:
            split_line = line[:-1].split('|')
            original_word = split_line[0]
            key_to_labeled_data[original_word] = line[:-1]
            selected_words[len(original_word)].append(original_word)
        selected_words.default_factory = None
    return selected_words, key_to_labeled_data


def print_dict_diffs(dict1, dict2, max_possible_word_length=100):
    for i in range(max_possible_word_length):
        if i + 1 in dict1 or i + 1 in dict2:
            print(f'{i+1}: {dict1[i+1] if i+1 in dict1 else 0} --> {dict2[i+1] if i+1 in dict2 else 0}')


def log_proportional(dict, degree, total_sum):
    dict_log = {}
    dict_log_rounded = {}
    for key, val in dict.items():
        dict_log[key] = math.log(val) ** degree
    all_log = sum(dict_log.values())
    for key, val in dict.items():
        dict_log[key] = dict_log[key] / all_log * total_sum
        dict_log_rounded[key] = math.ceil(dict_log[key])
    all_log_prop_rounded = sum(dict_log_rounded.values())
    n_to_substract = all_log_prop_rounded - total_sum
    keys_of_largest = sorted(dict_log_rounded.items(), key=lambda x: x[1], reverse=True)[:n_to_substract]
    for key, _ in keys_of_largest:
        dict_log_rounded[key] -= 1
    return dict_log_rounded


def get_dict(vocab_file):
    dict = defaultdict(list)
    with open(vocab_file, 'r') as f:
        for l in f:
            line = l.split(" ")
            dict[len(line[0])].append(line[0])
    dict.default_factory = None
    return dict


def randomly_select_words_from_dict(dict, already_selected_words=defaultdict(list)):
    already_selected_words.default_factory = list
    dict_stats = {k: len(v) for k, v in dict.items()}
    dict_stats_log_proportional = log_proportional(dict_stats, 5, 1000)

    items = dict_stats_log_proportional.items()
    for k, v in items:
        while v > len(already_selected_words[k]):
            picked_word = random.choice(dict[k])
            if picked_word not in already_selected_words[k] and re.fullmatch("[a-z]+", picked_word):
                already_selected_words[k].append(picked_word)
    return already_selected_words


def write_sample_to_files(length_to_words_dict, original_to_labeled_data, file):
    words = [w for k, w_list in length_to_words_dict.items() for w in w_list]
    with open(file, 'w') as f:
        for w in words:
            if w in original_to_labeled_data:
                w = original_to_labeled_data[w]
            f.write(f'{w}\n')


if __name__ == '__main__':
    dict = get_dict(vocab_file)
    dict_stats = {k: len(v) for k, v in dict.items()}
    dict_stats_log_proportional = log_proportional(dict_stats, 5, 1000)

    already_selected_words, key_to_labeled_data = get_already_selected_words()

    selected_words = randomly_select_words_from_dict(dict, already_selected_words)

    write_sample_to_files(selected_words, key_to_labeled_data, path_to_labeled_data2)

    print_dict_diffs({k: len(v) for k, v in already_selected_words.items()}, dict_stats_log_proportional)
