import argparse
import collections
import logging
import os

from logrec.dataprep import TRAIN_DIR, TEST_DIR
from logrec.util import io

logger = logging.getLogger(__name__)

class FileDefaultDict(collections.defaultdict):
    def __init__(self, output_dir):
        super().__init__()
        self.output_dir = output_dir

    def __missing__(self, key):
        self[key] = value = open(os.path.join(self.output_dir, f'context.{key}.src'), 'w')
        return value


def write_log_text_to_corpus_files(preprocessed_logs, output_dir):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    train_dir = os.path.join(output_dir, TRAIN_DIR)
    if not os.path.exists(train_dir):
        os.mkdir(train_dir)
    train_files = FileDefaultDict(train_dir)

    test_dir = os.path.join(output_dir, TEST_DIR)
    if not os.path.exists(test_dir):
        os.mkdir(test_dir)
    test_files = FileDefaultDict(test_dir)

    for ind, l in enumerate(preprocessed_logs):
        n_words = len(l.text_words)
        line = str(" ".join(l.text_words)) + "\n"
        if ind % 20 >= 3:
            train_files[n_words].write(line)
        else:
            test_files[n_words].write(line)
    for file in train_files.values():
        file.close()
    for file in test_files.values():
        file.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--log-text-corpus-dir', action='store', default='')
    args = parser.parse_args()

    preprocessed_logs = io.load_preprocessed_logs()
    write_log_text_to_corpus_files(preprocessed_logs, args.log_text_corpus_dir)