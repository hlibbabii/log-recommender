import argparse
import collections
import os

from util import io_utils


class FileDefaultDict(collections.defaultdict):
    def __init__(self, output_dir):
        super().__init__()
        self.output_dir = output_dir

    def __missing__(self, key):
        self[key] = value = open(f'{self.output_dir}/context.{key}.src', 'w')
        return value


def write_log_text_to_corpus_files(preprocessed_logs, output_dir):
    if not os.path.exists(f'{output_dir}'):
        os.mkdir(f'{output_dir}')
    if not os.path.exists(f'{output_dir}/train'):
        os.mkdir(f'{output_dir}/train')
    if not os.path.exists(f'{output_dir}/test'):
        os.mkdir(f'{output_dir}/test')
    train_files = FileDefaultDict(f'{output_dir}/train')
    test_files = FileDefaultDict(f'{output_dir}/test')
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

    preprocessed_logs = io_utils.load_preprocessed_logs()
    write_log_text_to_corpus_files(preprocessed_logs, args.log_text_corpus_dir)