from collections import Counter
import operator
import pickle
import itertools
from csv_io import output_frequencies, write_to_classification_spreadsheet, upload_to_google, \
    output_log_level_freqs_by_first_word, output_variable_freqs_by_first_word
from log_preprocessor import LOG_NUMBER_THRESHOLD

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


def calculate_log_level_freqs_by_first_word_cathegory(classified_logs, keys):
    occurences = {}
    levels = list(keys.keys())
    for log in classified_logs:
        if log.first_word_cathegory not in occurences:
            occurences[log.first_word_cathegory] = dict((level, 0) for level in levels)
            occurences[log.first_word_cathegory]['__all__'] = 0
        occurences[log.first_word_cathegory][log.log_level] += 1
        occurences[log.first_word_cathegory]['__all__'] += 1
    frequencies = {}
    for first_word_cathegory in occurences:
        frequencies[first_word_cathegory] = {}
        frequencies[first_word_cathegory]['__weighted_avg__'] = 0.0
        for level in levels:
            frequencies[first_word_cathegory][level] = occurences[first_word_cathegory][level] / occurences[first_word_cathegory]['__all__']
            frequencies[first_word_cathegory]['__weighted_avg__'] += frequencies[first_word_cathegory][level] * keys[level]
        frequencies[first_word_cathegory]['__all__'] = occurences[first_word_cathegory]['__all__']

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


UPLOAD_TO_GOOGLE = False


def get_significant_words(word_list, func):
    return list(filter(func, word_list))


if __name__ == '__main__':
    with open('pplogs.pkl', 'rb') as i:
        preprocessed_logs = pickle.load(i)
    project_stats = {}
    with open('project_stats.csv', 'r') as i:
        for line in i:
            split = line.split(",")
            project_stats[split[0]] = int(split[1])
    top_projects = get_top_projects_by_log_number(project_stats, LOG_NUMBER_THRESHOLD)

    frequencies = get_word_frequences(preprocessed_logs, lambda x: x.log_text_words)
    freq_stats = calc_frequency_stats(frequencies)
    output_frequencies(
        'generated_stats/frequencies.csv',
        sorted(freq_stats.items(), key=lambda x: x[1]['__median__'], reverse=True),
        top_projects
    )

    first_word_frequencies = get_word_frequences(preprocessed_logs, lambda x: [x.get_first_word()])
    first_word_freq_stats = calc_frequency_stats(first_word_frequencies)
    output_frequencies(
        'generated_stats/frequencies_first_word.csv',
        sorted(first_word_freq_stats.items(), key=lambda x: x[1]['__median__'], reverse=True),
        top_projects
    )

    is_not_other_by_found_in_projects = lambda w, stats=first_word_freq_stats, n_projects=len(first_word_frequencies):\
        stats[w]['__found_in_projects__'] / n_projects > 0.5

    is_not_other_by_word_frequency = lambda w, stats=first_word_freq_stats: stats[w]['__all__'] > 0.0002

    is_not_other_by_word_occurrences = lambda w, stats=first_word_freq_stats: stats[w]['__all_abs__'] > 700

    significant_first_words = get_significant_words(first_word_freq_stats.keys(), is_not_other_by_word_occurrences)

    classified_logs = classify_logs_by_first_word(preprocessed_logs, significant_first_words)
    keys = {"trace": 0.0,
            "debug": 0.1,
           "info": 0.3,
            "warn": 0.7,
            "error": 0.9,
            "fatal": 1.0}
    levels_distribution, levels = calculate_log_level_freqs_by_first_word_cathegory(classified_logs, keys)
    output_log_level_freqs_by_first_word("generated_stats/level_distribution.csv",
                                         sorted(levels_distribution.items(), key=lambda x: x[1]['__weighted_avg__']),
                                         levels)

    keys = [0, 1, 2, 3, 4]
    levels_distribution, levels = calculate_variable_freqs_by_first_word(classified_logs, keys)
    output_variable_freqs_by_first_word("generated_stats/n_vars_distribution.csv",
                                         levels_distribution.items(),
                                         levels)
    
    dir_name = 'logs'
    write_to_classification_spreadsheet(dir_name, classified_logs)
    if UPLOAD_TO_GOOGLE:
        upload_to_google(dir_name)