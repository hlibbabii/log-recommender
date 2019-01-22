import csv
import os
import pickle

__author__ = 'hlib'

PATH_TO_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
PATH_TO_PROJECT = PATH_TO_CURRENT_DIR = PATH_TO_CURRENT_DIR + '/../../'

CLASSES_FILE = os.path.join(PATH_TO_PROJECT, 'classes.csv')
MAJOR_CLASSES_LOGS_FILE = os.path.join(PATH_TO_PROJECT, 'major_classes_logs.pkl')
CLASSIFIED_LOGS_FILE = os.path.join(PATH_TO_PROJECT, 'classified_logs.pkl')
INTERESTING_WORDS_FILE = os.path.join(PATH_TO_PROJECT, 'interesting_context_words.csv')
PREPROCESSED_LOGS_FILE = os.path.join(PATH_TO_PROJECT, 'pplogs.pkl')
PROJECT_STATS_FILE = os.path.join(PATH_TO_PROJECT, 'project_stats.csv')
FREQUENCIES_FILE = os.path.join(PATH_TO_PROJECT, 'generated_stats', 'frequencies.csv')
FREQUENCIES_FILE_BINARY = os.path.join(PATH_TO_PROJECT, 'frequencies.pkl')
CONTEXT_VECTOR_FILE = os.path.join(PATH_TO_PROJECT, 'context_vectors.dat')
BINARY_CONTEXT_VECTOR_FILE = os.path.join(PATH_TO_PROJECT, 'binary_context_vectors.dat')
DISTRIBUTION_BY_LEVELS_FILE = os.path.join(PATH_TO_PROJECT, 'generated_stats', 'level_distribution.csv')
DISTRIBUTION_BY_N_VARS_FILE = os.path.join(PATH_TO_PROJECT, 'generated_stats', 'n_vars_distribution.csv')
PEARSONS_FILE = os.path.join(PATH_TO_PROJECT, 'generated_stats', 'output_pearsons.csv')
K_MEANS_CLUSTERING_STATS_FILE = os.path.join(PATH_TO_PROJECT, 'generated_stats', 'k_means_clustering_stats.csv')
FIRST_WORD_FREQUENCIES_FILE = os.path.join(PATH_TO_PROJECT, 'generated_stats', 'frequencies_first_word.csv')
FIRST_WORD_FREQUENCIES_FILE_BINARY = os.path.join(PATH_TO_PROJECT, 'frequencies_first_word.pkl')
CONTEXT_FREQUENCIES_FILE_BINARY = os.path.join(PATH_TO_PROJECT, 'frequencies_context.pkl')

def output_to_csv(filename, header, lambda1, dim1, dim2):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if header is not None:
            writer.writerow(header)
        for row in dim1:
            writer.writerow(lambda1(row, dim2))

#==================================================

def load_classes():
    with open(CLASSES_FILE, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            return row

def dump_classes(classes):
    output_to_csv(CLASSES_FILE, None, lambda a,b: b, [''], classes)

#==================================================

def load_major_classes_logs():
    with open(MAJOR_CLASSES_LOGS_FILE, 'rb') as f:
        return pickle.load(f)

def dump_major_classes_logs(major_classes_logs):
    with open(MAJOR_CLASSES_LOGS_FILE, "wb") as f:
        pickle.dump(major_classes_logs, f)

#==================================================

def load_classified_logs():
    with open(CLASSIFIED_LOGS_FILE, 'rb') as f:
        return pickle.load(f)

def dump_classified_logs(logs):
    with open(CLASSIFIED_LOGS_FILE, "wb") as f:
        pickle.dump(logs, f)

#==================================================

def load_interesting_words():
    with open(INTERESTING_WORDS_FILE, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            return row

def dump_interesting_words(words):
    output_to_csv(INTERESTING_WORDS_FILE, None, lambda a,b: b, [''], words)

#==================================================


def load_preprocessed_logs():
    with open(PREPROCESSED_LOGS_FILE, 'rb') as i:
        while True:
            try:
                yield pickle.load(i)
            except EOFError:
                break


def dump_preprocessed_logs(pp_logs):
    with open(PREPROCESSED_LOGS_FILE, 'wb') as o:
        for l in pp_logs:
            pickle.dump(l, o, pickle.HIGHEST_PROTOCOL)

#==================================================

def load_project_stats():
    read_dict_from_2_columns(PROJECT_STATS_FILE, delim=',')


def dump_project_stats(project_stats):
    dump_dict_into_2_columns(project_stats, PROJECT_STATS_FILE, delim=',')

#==================================================

def dump_frequencies_stats(freq_stats, top_projects):
    output_frequencies(
        FREQUENCIES_FILE,
        freq_stats,
        top_projects
    )

def dump_first_word_frequencies_stats(first_word_freq_stats, top_projects):
    output_frequencies(FIRST_WORD_FREQUENCIES_FILE,
        first_word_freq_stats,
        top_projects
    )

def output_frequencies(filename, frequencies, sorted_project_list):
    output_to_csv(
        filename,
        ['word', 'median', 'mean', 'found times', 'found in projects'] + sorted_project_list,
        lambda d1, d2: [d1[0], d1[1]['__median__'],
                             d1[1]['__all__'],
                             d1[1]['__all_abs__'],
                             d1[1]['__found_in_projects__']] +
            list(map(lambda x: d1[1][x] if x in d1[1] else 0.0, d2)),
        sorted(frequencies.items(), key=lambda x: x[1]['__median__'], reverse=True),
        sorted_project_list
    )

#==================================================

def dump_frequencies_stats_binary(freq_stats):
    with open(FREQUENCIES_FILE_BINARY, 'wb') as o:
        pickle.dump(freq_stats, o, pickle.HIGHEST_PROTOCOL)

def dump_first_word_frequencies_stats_binary(freq_stats):
    with open(FIRST_WORD_FREQUENCIES_FILE_BINARY, 'wb') as o:
        pickle.dump(freq_stats, o, pickle.HIGHEST_PROTOCOL)

def dump_context_frequencies_stats_binary(freq_stats):
    with open(CONTEXT_FREQUENCIES_FILE_BINARY, 'wb') as o:
        pickle.dump(freq_stats, o, pickle.HIGHEST_PROTOCOL)

def load_first_word_frequencies_stats_binary():
    with open(FIRST_WORD_FREQUENCIES_FILE_BINARY, 'rb') as f:
        return pickle.load(f)

def load_frequencies_stats_binary():
    with open(FREQUENCIES_FILE_BINARY, 'rb') as f:
        return pickle.load(f)

def load_context_frequencies_stats_binary():
    with open(CONTEXT_FREQUENCIES_FILE_BINARY, 'rb') as f:
        return pickle.load(f)

#==================================================

def dump_context_vectors(context_vectors):
    with open(CONTEXT_VECTOR_FILE, 'w') as f:
        for log_vector in context_vectors:
            f.write("[" + log_vector['id'] + "] " + " ".join(log_vector['values']) + "\n")

def load_context_vectors():
    with open(CONTEXT_VECTOR_FILE, 'r') as f:
        split_lines = [line.split() for line in f]
        return [{'id': line[0][1:-1], 'values': line[1:]} for line in split_lines]

#==================================================

def dump_binary_context_vectors(binary_context_vectors):
    with open(BINARY_CONTEXT_VECTOR_FILE, 'w') as f:
        for log_vector in binary_context_vectors:
            f.write("[" + log_vector['id'] + "] " + " ".join(map(lambda l: "1" if l else "0", log_vector['values'])) + "\n")


def load_binary_context_vectors():
    with open(BINARY_CONTEXT_VECTOR_FILE, 'r') as f:
        return [list(map(lambda x: int(x), row.split()[1:])) for row in f]

#==================================================

def dump_level_distributions(levels_distribution, levels):
    output_to_csv(DISTRIBUTION_BY_LEVELS_FILE,
        ['word', 'weighted avg', 'all'] + levels,
        lambda freqs,levels: [freqs[0], freqs[1]['__weighted_avg__'], freqs[1]['__all__']] +
            list(map(lambda x: freqs[1][x] if x in freqs[1] else 0.0, levels)),
        sorted(levels_distribution.items(), key=lambda x: x[1]['__weighted_avg__']),
        levels
    )

def dump_n_vars_distribution(n_vars_distribution, n_vars):
    output_to_csv(DISTRIBUTION_BY_N_VARS_FILE,
        ['word', 'all'] + n_vars + ['more vars'],
        lambda dist,levels: [dist[0], dist[1]['__all__']]
                            + list(map(lambda x: dist[1][x] if x in dist[1] else 0.0, levels)),
        n_vars_distribution.items(),
        n_vars
    )

#==================================================

def dump_pearsons(pearsons, classes):
        output_to_csv(PEARSONS_FILE,
        ['word'] + classes,
        lambda d1,d2: [d1[1]] + d2[d1[0]],
        enumerate(classes),
        pearsons
    )

def dump_k_means_clustering_stats(clustering_stats, classes, word_count, gini):
        output_to_csv(K_MEANS_CLUSTERING_STATS_FILE,
        ['word'] + list(range(len(clustering_stats))) + ['total', 'gini'],
        lambda stats,classes,wc=word_count,gi=gini:
            [stats] + list(map(lambda x: x[stats] if stats in x else 0, classes)) + [wc[stats], gi[stats]],
        classes,
        clustering_stats
    )

#==================================================


def dump_dict_into_2_columns(dct, file, val_type=str, delim='\t', append=False):
    with open(file, 'w+' if append else 'w') as f:
        lst = dct.items() if isinstance(dct, dict) else dct
        for word, freq in lst:
            value = ' '.join(freq) if val_type == list else str(freq)
            f.write(f'{str(word)}{delim}{value}\n')


def read_dict_from_2_columns(file, val_type=str, delim='\t'):
    words = {}
    with open(file, 'r') as f:
        for line in f:
            line = line[:-1] if line[-1] else line
            splits = line.split(delim)
            if val_type == list:
                second_column = splits[1].split(' ')
            else:
                try:
                    second_column = int(splits[1])
                except:
                    second_column = splits[1]
            words[splits[0]] = second_column
    return words


def read_list(file):
    res = []
    with open(file, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            splits = line.split(' ')
            res.append(splits if len(splits) > 1 else splits[0])
    return res


def dump_list(lst, file):
    with open(file, 'w') as f:
        for elm in lst:
            if isinstance(elm, list) or isinstance(elm, tuple):
                f.write(f"{' '.join(elm)}\n")
            else:
                f.write(f"{elm}\n")


