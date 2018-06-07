import argparse
import logging
import os
from operator import attrgetter

from bokeh.util.logconfig import level

from classify_and_select_major_logs import select_logs_from_major_classes
import io_utils
from java_parser import JavaParser, EOF
from log_statement import preprocess_ctx, replace_4whitespaces_with_tabs, spl_verbose, merge_tabs, camel_case_split, \
    underscore_split


def write_log_text_to_corpus_file(preprocessed_logs, output_filename):
    with open(output_filename, 'w') as f:
        for l in preprocessed_logs:
            f.write(str(l.text) + "\n")


def write_log_context_to_corpus_file(preprocessed_logs, output_filename, context_lines_to_consider):
    with open(output_filename, 'w') as f:
        for l in preprocessed_logs:
            f.write(" ".join(l.get_context_words(context_lines_to_consider)) + "\n")

split_line_canel_case = lambda context_line: [item.lower() for identifier in context_line for item in camel_case_split(identifier, add_separator=True)]
split_line_underscore = lambda context_line: [item for identifier in context_line for item in underscore_split(identifier, add_separator=True)]

def process(context, interesting_context_words):
    processed = [w for line in list(map(lambda x: preprocess_ctx(x, func_list=[
        replace_4whitespaces_with_tabs,
        spl_verbose,
        split_line_canel_case,
        split_line_underscore,
        merge_tabs
    ]), context)) for w in (line + [EOF])]
    java_parser = JavaParser()
    processed = java_parser.strip_off_string_literals(processed)
    processed = java_parser.strip_off_multiline_comments(processed)
    processed = java_parser.strip_off_one_line_comments(processed)
    processed = java_parser.strip_off_number_literals(processed)
    processed = java_parser.strip_off_identifiers(processed, interesting_context_words)
    return processed

def process_full_identifiers(context, interesting_context_words):
    processed = [w for line in list(map(lambda x: preprocess_ctx(x, func_list=[
        replace_4whitespaces_with_tabs,
        spl_verbose,
        split_line_canel_case,
        split_line_underscore,
        merge_tabs
    ]), context)) for w in (line + [EOF])]
    java_parser = JavaParser()
    processed = java_parser.strip_off_string_literals(processed)
    processed = java_parser.strip_off_multiline_comments(processed)
    processed = java_parser.strip_off_one_line_comments(processed)
    processed = java_parser.strip_off_number_literals(processed)
    processed = java_parser.strip_off_identifiers(processed, interesting_context_words)
    return processed

logging.basicConfig(level=logging.DEBUG)

def write_log_context_to_fastai_input(train_logs, output_dir, interesting_context_words):
    with open(output_dir + "contexts.src", 'w') as c_file,\
            open(output_dir + "levels.src", 'w') as l_file, \
            open(output_dir + "index", 'w') as i_file:
        logs_n_total = len(train_logs)
        for ind, log in enumerate(train_logs):
            if ind % 10 == 0:
                logging.info(f'Processing log {ind} out of {logs_n_total} ({ind * 100.0 / logs_n_total:.4}%)')
            c_file.write(repr(" ".join(process_full_identifiers(log.context.context_before, interesting_context_words)))[1:-1] + " <ect>\n")
            l_file.write(log.neg_or_pos() + "\n")
            i_file.write(log.id + "\n")

def write_context_index(logs, output_filename):
    with open(output_filename, 'w') as f:
        for l in logs:
            f.write(l.id + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--context-lines-to-consider', action='store', type=int, default=4)

    parser.add_argument('--output-corpus-file', action='store', default='../../gengram/corpus.txt')
    parser.add_argument('--output-context-corpus-file', action='store', default='../../AutoenCODE/data/corpus.src')
    parser.add_argument('--context-index-file', action='store', default='../context.index')
    parser.add_argument('--fastai-input-file', action='store', default='../../fastai-sample/data')
    args = parser.parse_args()

    interesting_context_words = io_utils.load_interesting_words()

    preprocessed_logs = io_utils.load_preprocessed_logs()
    write_log_text_to_corpus_file(preprocessed_logs, args.output_corpus_file)
    write_log_context_to_corpus_file(preprocessed_logs, args.output_context_corpus_file,
                                     args.context_lines_to_consider)
    classes = ['debug', 'info', 'warn', 'error']
    n_logs_for_1_class = 12500
    fraction_for_testing = 0.2
    logs_by_levels,_ = select_logs_from_major_classes(preprocessed_logs, attrgetter('level'),
                                                              classes, n_logs_for_1_class)
    logs_for_fast_ai_training = logs_by_levels[int(n_logs_for_1_class * fraction_for_testing * len(classes)):]
    logs_for_fast_ai_testing = logs_by_levels[:int(n_logs_for_1_class * fraction_for_testing * len(classes))]

    train_dir = f'{args.fastai_input_file}/train/'
    test_dir = f'{args.fastai_input_file}/test/'
    if not os.path.exists(train_dir):
        os.makedirs(train_dir)
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    write_log_context_to_fastai_input(logs_for_fast_ai_training, train_dir, interesting_context_words)
    write_log_context_to_fastai_input(logs_for_fast_ai_testing, test_dir, interesting_context_words)

    write_context_index(preprocessed_logs, args.context_index_file)