import operator
import pickle
from pprint import pprint
from math import log
from csv_io import output_frequencies, write
from log_picker import test_pick_log
from log_preprocessor import output_to_file, THRESHOLD

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
        if w in dict:
            dict[w] += 1
        else:
            dict[w] = 1
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


if __name__ == '__main__':
    with open('pplogs.pkl', 'rb') as i:
        preprocessed_logs = pickle.load(i)
    project_stats = {}
    with open('project_stats1.csv', 'r') as i:
        for line in i:
            split = line.split(",")
            project_stats[split[0]] = int(split[1])
    top_projects = get_top_projects(project_stats)
    frequencies = get_frequencies_for_log_texts(preprocessed_logs)
    output_frequencies(
        sorted(calc_frequency_stats(frequencies).items(), key=lambda x: x[1]['__median__'], reverse=True),
        top_projects
    )
    pprint(project_stats)
    first_word_frequencies = get_first_word_frequencies(preprocessed_logs)
    # pprint(sorted(first_word_frequencies.items(), key=operator.itemgetter(1), reverse=True))
    sorted_idf_tuples, idfs = get_idfs(list(map(lambda l: l.context_words, preprocessed_logs)))

    output_to_file(preprocessed_logs, sorted_idf_tuples)
    test_pick_log(preprocessed_logs, idfs)
    write(preprocessed_logs)