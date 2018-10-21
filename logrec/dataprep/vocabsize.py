import argparse
import logging
import os
import time
from multiprocessing.pool import Pool

from logrec.dataprep.to_repr import REPR_EXTENSION
from logrec.local_properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_VOCABSIZE_ARGS


class VocabMerger(object):
    DEFAULT_PERCENTS = [0.01, 0.02, 0.05, 0.15, 0.5, 0.95, 1.0]

    def __init__(self):
        self.sizes = []
        self.merged_vocabs = set()

    def merge(self, vocab):
        if not isinstance(vocab, set):
            raise TypeError(f'Vocab must be a set, but is {type(vocab)}')

        new_words = vocab.difference(self.merged_vocabs)
        logging.debug(f"New words: {list(new_words)[:10]} ...")
        self.merged_vocabs = self.merged_vocabs.union(vocab)
        self.sizes.append(len(self.merged_vocabs))

    def write_stats(self, path_to_stats_file):
        stats = self.__generate_stats()
        with open(path_to_stats_file, 'w') as f:
            f.write(f"{str(self.sizes[-1])}\n")
            for line in stats:
                f.write(f"{line[0]} {line[1]}\n")

    def __generate_stats(self):
        total = len(self.sizes)
        stats = []
        for percent in self.DEFAULT_PERCENTS:
            n_files = int(percent * total)
            exact_percent = float(n_files) / total
            stats.append((exact_percent, self.sizes[n_files - 1] if n_files > 0 else 0))
        return stats


def calc_total_files(full_src_dir):
    files_total = 0
    for root, dirs, files in os.walk(full_src_dir):
        for file in files:
            if file.endswith(f".{REPR_EXTENSION}"):
                files_total += 1
    return files_total


def get_all_files(full_src_dir):
    res = []
    for root, dirs, files in os.walk(full_src_dir):
        for file in files:
            if file.endswith(f".{REPR_EXTENSION}"):
                res.append(os.path.join(root, file))
    return res


def get_vocab(path_to_file):
    vocab = set()
    with open(path_to_file, 'r') as f:
        for line in f:
            if line[-1] == '\n':
                line = line[:-1]
            split = line.split(' ')
            for word in split:
                vocab.add(word)
    return vocab


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-from', action='store', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('src', action='store', help=f'path to the preprocessed files')

    args = parser.parse_known_args(*DEFAULT_VOCABSIZE_ARGS)
    args = args[0]

    logging.basicConfig(level=logging.DEBUG)

    full_src_dir = f'{args.base_from}/{args.src}'
    if not os.path.exists(full_src_dir):
        logging.error(f"Dir does not exist: {full_src_dir}")
        exit(3)
    logging.info(f"Reading files from: {os.path.abspath(full_src_dir)}")

    all_files = get_all_files(full_src_dir)
    if not all_files:
        logging.warning("No preprocessed files found.")
        exit(4)
    files_total = len(all_files)
    current_file = 0
    start_time = time.time()
    vocab_merger = VocabMerger()
    with Pool() as pool:
        it = pool.imap_unordered(get_vocab, all_files)
        for vocab in it:
            vocab_merger.merge(vocab)
            current_file += 1
            logging.info(f"Processed {current_file} out of {files_total}")
            time_elapsed = time.time() - start_time
            logging.info(f"Time elapsed: {time_elapsed:.2f} s, estimated time until completion: "
                         f"{time_elapsed / current_file * files_total - time_elapsed:.2f} s")

    vocab_merger.write_stats(f'{full_src_dir}/vocabsize')
