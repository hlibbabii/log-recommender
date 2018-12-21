import argparse
import logging
import os
from operator import attrgetter

from logrec.classify_and_select_major_logs import select_logs_from_major_classes
from logrec.dataprep import TRAIN_DIR, TEST_DIR
from logrec.dataprep.preprocessors import apply_preprocessors
from logrec.dataprep.preprocess_params import pp_params
from logrec.util import io_utils


def write_log_context_to_corpus_file(preprocessed_logs, output_filename, context_lines_to_consider):
    with open(output_filename, 'w') as f:
        for l in preprocessed_logs:
            f.write(" ".join(l.get_context_words(context_lines_to_consider)) + "\n")

def write_log_context_to_fastai_input(train_logs, output_dir, interesting_context_words):
    with open(output_dir + "contexts.src", 'w') as c_file,\
            open(output_dir + "levels.src", 'w') as l_file, \
            open(output_dir + "index", 'w') as i_file:
        logs_n_total = len(train_logs)
        for ind, log in enumerate(train_logs):
            if ind % 10 == 0:
                logging.info(f'Processing log {ind} out of {logs_n_total} ({ind * 100.0 / logs_n_total:.4}%)')
            c_file.write(apply_preprocessors(pp_params, log.context.context_before, {'interesting_context_words': interesting_context_words}))
            l_file.write(log.neg_or_pos() + "\n")
            i_file.write(log.id + "\n")

def write_context_index(logs, output_filename):
    with open(output_filename, 'w') as f:
        for l in logs:
            f.write(l.id + "\n")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--context-lines-to-consider', action='store', type=int, default=4)

    parser.add_argument('--output-context-corpus-file', action='store', default='../../AutoenCODE/data/corpus.src')
    parser.add_argument('--context-index-file', action='store', default='../context.index')
    parser.add_argument('--fastai-input-file', action='store', default='../../fastai-sample/data')
    args = parser.parse_args()

    interesting_context_words = io_utils.load_interesting_words()

    preprocessed_logs = io_utils.load_preprocessed_logs()
    write_log_context_to_corpus_file(preprocessed_logs, args.output_context_corpus_file,
                                     args.context_lines_to_consider)
    classes = ['debug', 'info', 'warn', 'error']
    n_logs_for_1_class = 12500
    fraction_for_testing = 0.2
    logs_by_levels,_ = select_logs_from_major_classes(preprocessed_logs, attrgetter('level'),
                                                              classes, n_logs_for_1_class)
    logs_for_fast_ai_training = logs_by_levels[int(n_logs_for_1_class * fraction_for_testing * len(classes)):]
    logs_for_fast_ai_testing = logs_by_levels[:int(n_logs_for_1_class * fraction_for_testing * len(classes))]

    train_dir = os.path.join(args.fastai_input_file, TRAIN_DIR)
    test_dir = os.path.join(args.fastai_input_file, TEST_DIR)
    if not os.path.exists(train_dir):
        os.makedirs(train_dir)
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    write_log_context_to_fastai_input(logs_for_fast_ai_training, train_dir, interesting_context_words)
    write_log_context_to_fastai_input(logs_for_fast_ai_testing, test_dir, interesting_context_words)

    write_context_index(preprocessed_logs, args.context_index_file)