import argparse
import logging
import os

from logrec.dataprep import TRAIN_DIR, TEST_DIR
from logrec.dataprep.preprocessors import apply_preprocessors
from logrec.dataprep.preprocessors.general import to_token_list, from_file
from logrec.util import io_utils

logger = logging.getLogger(__name__)

LOG_PLACEHOLDER = "<LOG>"

preprocessors = [
        "replace_4whitespaces_with_tabs",
        "spl_verbose",
        "newline_and_tab_remover",
    "split_line_camel_case",
        "split_line_underscore",
        "java.strip_off_string_literals",
        "java.strip_off_multiline_comments",
        "java.strip_off_one_line_comments",
    "java.process_number_literals"
    ]

def get_true_context(log):
    pp_before = apply_preprocessors(from_file(log.context.context_before[1:]), preprocessors)
    pp_after = apply_preprocessors(from_file(log.context.context_after[:-1]), preprocessors)
    return apply_preprocessors(pp_before + [LOG_PLACEHOLDER] + pp_after, [to_token_list])


def get_false_context(log):
    pp_before = apply_preprocessors(from_file(log.context.context_before[:-1]), preprocessors)
    pp_after = apply_preprocessors([from_file(log.context.context_before[-1])] + log.context.context_after[:-2],
                                   preprocessors)
    return apply_preprocessors(pp_before + [LOG_PLACEHOLDER] + pp_after, [to_token_list])


def write_corpus(preprocessed_logs, output_dir):
    dirs = [
        os.path.join(output_dir, TRAIN_DIR, 'true'),
        os.path.join(output_dir, TRAIN_DIR, 'false'),
        os.path.join(output_dir, TEST_DIR, 'true'),
        os.path.join(output_dir, TEST_DIR, 'false')
    ]
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)
    name = "context.0.src"
    with open(os.path.join(dirs[0], name), 'w') as train_true, open(os.path.join(dirs[1], name),
                                                                    'w') as train_false, open(
            os.path.join(dirs[2], name), 'w') as test_true, open(os.path.join(dirs[3], name), 'w') as test_false:
        for ind, log in enumerate(preprocessed_logs):
            if ind % 2 == 0:
                context = get_true_context(log)
                if ind % 40 > 6:
                    train_true.write(context)
                else:
                    test_true.write(context)

            else:
                context = get_false_context(log)
                if ind % 40 > 6:
                    train_false.write(context)
                else:
                    test_false.write(context)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--log-text-corpus-dir', action='store', default='')
    args = parser.parse_args()

    preprocessed_logs = io_utils.load_preprocessed_logs()
    write_corpus(preprocessed_logs, args.log_text_corpus_dir)