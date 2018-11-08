import logging

from logrec.util import io_utils


def calculate_log_level_freqs_by_first_word_cathegory(classified_logs, keys):
    occurences = {}
    levels = list(keys.keys())
    for log in classified_logs:
        if log.first_word_cathegory not in occurences:
            occurences[log.first_word_cathegory] = dict((level, 0) for level in levels)
            occurences[log.first_word_cathegory]['__all__'] = 0
        occurences[log.first_word_cathegory][log.level] += 1
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


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    logging.info("Calculating and saving stats")

    classified_logs = io_utils.load_classified_logs()

    keys = {"trace": 0.0,
            "debug": 0.1,
           "info": 0.3,
            "warn": 0.7,
            "error": 0.9,
            "fatal": 1.0}
    levels_distribution, levels = calculate_log_level_freqs_by_first_word_cathegory(classified_logs, keys)
    io_utils.dump_level_distributions(levels_distribution, levels)

    keys = [0, 1, 2, 3, 4]
    n_vars_distribution, n_vars = calculate_variable_freqs_by_first_word(classified_logs, keys)
    io_utils.dump_n_vars_distribution(n_vars_distribution, n_vars)