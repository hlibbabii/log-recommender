import operator
import pickle
from pprint import pprint
from math import log
from csv_io import output_frequencies, write_to_classification_spreadsheet, upload_to_google, \
    output_log_level_freqs_by_first_word, output_variable_freqs_by_first_word
from log_picker import test_pick_log
from log_preprocessor import THRESHOLD

__author__ = 'hlib'

def get_frequencies_for_log_texts(logs):
    dict = {}
    for l in logs:
        for w in l.log_text_words:
            if l.project not in dict:
                dict[l.project] = {}
            if w in dict[l.project]:
                dict[l.project][w] += 1
            else:
                dict[l.project][w] = 1
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
        frequencies[word]['__found_in_projects__'] = len(frequencies[word]) - 2
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


def get_first_word_frequencies(logs):
    dict = {}
    for l in logs:
        w = l.log_first_word
        if l.project not in dict:
            dict[l.project] = {}
        if w in dict[l.project]:
            dict[l.project][w] += 1
        else:
            dict[l.project][w] = 1
    return dict


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

def get_top_projects(project_stats):
    return list(map(lambda x : x[0],
              sorted(filter(lambda x: x[1] >= THRESHOLD, project_stats.items()), key=lambda x: x[1], reverse=True)
              ))


def classify_logs_by_first_word(preprocessed_logs, first_word_freq_stats):
    most_freq_words=list(map(lambda x:x[0], filter(lambda x:x[1]['__median__'], first_word_freq_stats.items())))
    pprint(most_freq_words)
    for log in preprocessed_logs:
        first_word = log.log_text_words[0] if len(log.log_text_words) > 0 else ""
        log.first_word_cathegory = first_word if first_word in most_freq_words else "OTHER__"
    return preprocessed_logs


def calculate_log_level_freqs_by_first_word(classified_logs, keys):
    occurences = {}
    levels = list(keys.keys())
    for log in classified_logs:
        if log.first_word_cathegory not in occurences:
            occurences[log.first_word_cathegory] = dict((level, 0) for level in levels)
            occurences[log.first_word_cathegory]['__all__'] = 0
        occurences[log.first_word_cathegory][log.log_level] += 1
        occurences[log.first_word_cathegory]['__all__'] += 1
    frequencies = {}
    for first_word in occurences:
        frequencies[first_word] = {}
        frequencies[first_word]['__weighted_avg__'] = 0.0
        for level in levels:
            frequencies[first_word][level] = occurences[first_word][level] / occurences[first_word]['__all__']
            frequencies[first_word]['__weighted_avg__'] += frequencies[first_word][level] * keys[level]
        frequencies[first_word]['__all__'] = occurences[first_word]['__all__']

    return frequencies, levels


def calculate_variable_freqs_by_first_word(classified_logs, keys):
    occurences = {}
    for log in classified_logs:
        if log.first_word_cathegory not in occurences:
            occurences[log.first_word_cathegory] = dict((key, 0) for key in keys)
            occurences[log.first_word_cathegory]['__more_vars__'] = 0
            occurences[log.first_word_cathegory]['__all__'] = 0
        if log.n_variables in occurences[log.first_word_cathegory]:
            occurences[log.first_word_cathegory][log.n_variables] += 1
        else:
            occurences[log.first_word_cathegory]['__more_vars__'] += 1
        occurences[log.first_word_cathegory]['__all__'] += 1
    frequencies = {}
    for first_word in occurences:
        frequencies[first_word] = {}
        for key in keys:
            frequencies[first_word][key] = occurences[first_word][key] / occurences[first_word]['__all__']
        frequencies[first_word]['__more_vars__'] \
                = occurences[first_word]['__more_vars__'] / occurences[first_word]['__all__']
        frequencies[first_word]['__all__'] = occurences[first_word]['__all__']

    return frequencies, keys


def output_to_corpus_file(preprocessed_logs, output_filename):
    with open(output_filename, 'w') as f:
        for l in preprocessed_logs:
            f.write(str(l.log_text) + "\n")


if __name__ == '__main__':
    with open('pplogs.pkl', 'rb') as i:
        preprocessed_logs = pickle.load(i)
    project_stats = {}
    with open('project_stats.csv', 'r') as i:
        for line in i:
            split = line.split(",")
            project_stats[split[0]] = int(split[1])
    top_projects = get_top_projects(project_stats)

    frequencies = get_frequencies_for_log_texts(preprocessed_logs)
    output_frequencies(
        'frequencies.csv',
        sorted(calc_frequency_stats(frequencies).items(), key=lambda x: x[1]['__median__'], reverse=True),
        top_projects
    )

    first_word_frequencies = get_first_word_frequencies(preprocessed_logs)
    first_word_freq_stats = calc_frequency_stats(first_word_frequencies)
    output_frequencies(
        'frequencies_first_word.csv',
        sorted(first_word_freq_stats.items(), key=lambda x: x[1]['__median__'], reverse=True),
        top_projects
    )
    
    classified_logs = classify_logs_by_first_word(preprocessed_logs, first_word_freq_stats)
    keys = {"trace": 0.0,
            "debug": 0.1,
           "info": 0.3,
            "warn": 0.7,
            "error": 0.9,
            "fatal": 1.0}
    levels_distribution, levels = calculate_log_level_freqs_by_first_word(classified_logs, keys)
    output_log_level_freqs_by_first_word("level_distribution.csv",
                                         sorted(levels_distribution.items(), key=lambda x: x[1]['__weighted_avg__']),
                                         levels)

    keys = [0, 1, 2, 3, 4]
    levels_distribution, levels = calculate_variable_freqs_by_first_word(classified_logs, keys)
    output_variable_freqs_by_first_word("n_vars_distribution.csv",
                                         levels_distribution.items(),
                                         levels)
    
    dir_name = 'logs'
    write_to_classification_spreadsheet(dir_name, classified_logs)
    upload_to_google(dir_name)

    sorted_idf_tuples, idfs = get_idfs(list(map(lambda l: l.context_words, preprocessed_logs)))
    output_to_corpus_file(preprocessed_logs, '../gengram/corpus.txt')
    test_pick_log(preprocessed_logs, idfs)