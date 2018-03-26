import operator

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