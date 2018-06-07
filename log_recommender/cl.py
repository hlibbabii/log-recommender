import argparse
import logging
import io_utils

def get_significant_words(word_list, func):
    return list(filter(func, word_list))


# def is_not_other_by_found_in_projects(min_found_in_projects_frequency):
#     return lambda w, stats=first_word_freq_stats, n_projects=len(first_word_frequencies):\
#         stats[w]['__found_in_projects__'] / n_projects > min_found_in_projects_frequency

def is_not_other_by_word_frequency(min_word_frequency):
    return lambda w, stats=first_word_freq_stats: stats[w]['__all__'] > min_word_frequency

def is_not_other_by_word_occurrences(min_word_occurencies):
    return lambda w, stats=first_word_freq_stats: stats[w]['__all_abs__'] > min_word_occurencies

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-word-occurencies', action='store', type=int, default=700)
    parser.add_argument('--min-word-frequency', action='store', type=float, default=0.0009)
    parser.add_argument('--min-found-in-projects-frequency', action='store', type=float, default=0.5) #not used for now

    args = parser.parse_args()

    first_word_freq_stats = io_utils.load_first_word_frequencies_stats_binary()

    logging.info("Getting log classes...")
    classes = get_significant_words(first_word_freq_stats.keys(),
                                                    is_not_other_by_word_occurrences(args.min_word_occurencies))

    io_utils.dump_classes(classes)

    logging.info("Getting interesting words from the contexts")
    context_word_freq_stats = io_utils.load_context_frequencies_stats_binary()
    interesting_words_from_context = get_significant_words(context_word_freq_stats.keys(),
        lambda w, stats=context_word_freq_stats: stats[w]['__all__'] > args.min_word_frequency)
    io_utils.dump_interesting_words(interesting_words_from_context)

    print("Classes: " + str(len(classes)))
    print(classes)

    print("interesting words from context: " + str(len(interesting_words_from_context)))
    print(interesting_words_from_context)