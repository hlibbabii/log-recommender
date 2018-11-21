import argparse
import logging
import multiprocessing
import os
import pickle
import queue
import shutil
import time
from collections import Counter, defaultdict
from multiprocessing.pool import Pool

from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.to_repr import REPR_EXTENSION
from logrec.local_properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_VOCABSIZE_ARGS
from logrec.util import io_utils

logger = logging.getLogger(__name__)

PARTVOCAB_EXT = 'partvocab'

def merge_dicts_(dict1, dict2):
    '''
    this method returns modified dict1! and new words are added to the dictionary
    :param dict1:
    :param dict2:
    :return:
    '''
    new_words = []
    for k, v in dict2.items():
        if k not in dict1:
            dict1[k] = v
            new_words.append(k)
    return dict1, new_words


class PartialVocab(object):
    DEFAULT_PERCENTS = [0.01, 0.02, 0.05, 0.15, 0.5, 0.95, 1.0]
    CLASS_VERSION = 2

    def __init__(self, word_counts):
        if not isinstance(word_counts, Counter):
            raise TypeError(f'Vocab must be a Counter, but is {type(word_counts)}')

        self.merged_word_counts = word_counts
        self.stats = [(1, len(self.merged_word_counts), self.merged_word_counts[placeholders['non_eng']])]
        self.n_files = 1
        self.id = self.__generate_id()

    def __generate_id(self):
        return ''.join(str(time.time()).split('.'))

    def renew_id(self):
        self.id = self.__generate_id()

    def set_path_to_dump(self, path):
        self.path_to_dump = path

    def add_vocab(self, partial_vocab):
        if not isinstance(partial_vocab, PartialVocab):
            raise TypeError(f'Vocab must be a PartialVocab, but is {type(partial_vocab)}')

        start = time.time()

        self.merged_word_counts, new_words = merge_dicts_(self.merged_word_counts, partial_vocab.merged_word_counts)
        logger.debug(f"New words: {new_words[:10]} ..., total: {len(new_words)}")
        cur_vocab_size = len(self.merged_word_counts)

        logger.info(f"Merging took {time.time() - start} s, current vocab size: {cur_vocab_size}")

        self.n_files += partial_vocab.n_files
        new_stats_entry = (self.n_files, cur_vocab_size, self.merged_word_counts[placeholders['non_eng']])
        self.stats.extend(partial_vocab.stats + [new_stats_entry])

    def write_stats(self, path_to_stats_file):
        stats = self.__generate_stats()
        with open(path_to_stats_file, 'w') as f:
            for percent, (v, n) in stats:
                f.write(f"{percent} {v} {n}\n")

    def write_vocab(self, path_to_vocab_file):
        sorted_vocab = sorted(self.merged_word_counts.items(), key=lambda x: x[1], reverse=True)
        io_utils.dump_dict_into_2_columns(sorted_vocab, path_to_vocab_file)

    def __generate_stats(self):
        d = defaultdict(list)
        for entry in self.stats:
            d[entry[0]].append((entry[1], entry[2]))
        fin = {(float(k) / self.n_files): avg_ssum(v) for k, v in d.items()}
        return sorted(fin.items())


# TODO remove this ugliness!!
def avg_ssum(nested_list):
    sm = (0, 0)
    for i, k in nested_list:
        sm = (sm[0] + i, sm[1] + k)
    return (sm[0] / float(len(nested_list)), sm[1] / float(len(nested_list)))

def calc_total_files(full_src_dir):
    files_total = 0
    for root, dirs, files in os.walk(full_src_dir):
        for file in files:
            if file.endswith(f".{REPR_EXTENSION}"):
                files_total += 1
    return files_total


def get_all_files(full_src_dir, ext):
    res = []
    for root, dirs, files in os.walk(full_src_dir):
        for file in files:
            if file.endswith(f".{ext}"):
                res.append(os.path.join(root, file))
    return res


def get_vocab(path_to_file):
    vocab = Counter()
    with open(path_to_file, 'r') as f:
        for line in f:
            if line[-1] == '\n':
                line = line[:-1]
            split = line.split(' ')
            vocab.update(split)
    return vocab


def create_merged_vocab(path_to_dump):
    if (os.path.exists(path_to_dump)):
        vocab_merger = pickle.load(open(path_to_dump, 'rb'))
        vocab_merger.set_path_to_dump(path_to_dump)
        if not isinstance(vocab_merger, PartialVocab):
            raise TypeError(f"Object {str(vocab_merger)} must be VocabMerger version {vocab_merger.VERSION}")
        return vocab_merger
    else:
        return PartialVocab(path_to_dump)


class Merger(multiprocessing.Process):
    def __init__(self, tasks, path_to_dump):
        multiprocessing.Process.__init__(self)
        self.tasks = tasks
        self.path_to_dump = path_to_dump

    def run(self):
        while True:
            try:
                first = self.tasks.get_nowait()
            except queue.Empty:
                break

            try:
                second = self.tasks.get_nowait()
            except queue.Empty:
                self.tasks.put_nowait(first)
                break

            first_id = first.id
            second_id = second.id

            first.add_vocab(second)

            first.renew_id()
            path_to_new_file = f'{self.path_to_dump}/{first_id}_{second_id}_{first.id}.{PARTVOCAB_EXT}'
            pickle.dump(first, open(path_to_new_file, 'wb'))
            finish_file_dumping(path_to_new_file)

            self.tasks.put_nowait(first)


def finish_file_dumping(path_to_new_file):
    base = os.path.basename(path_to_new_file)
    dir = os.path.dirname(path_to_new_file)
    spl = base.split('.')[0].split('_')
    if len(spl) != 3:
        raise AssertionError(f'Wrong file: {path_to_new_file}')
    first_id, second_id, new_id = spl[0], spl[1], spl[2]
    os.remove(f'{dir}/{first_id}.{PARTVOCAB_EXT}')
    os.remove(f'{dir}/{second_id}.{PARTVOCAB_EXT}')
    new_file = f'{dir}/{new_id}.{PARTVOCAB_EXT}'
    os.rename(f'{dir}/{first_id}_{second_id}_{new_id}.{PARTVOCAB_EXT}', new_file)
    return new_file


def run(full_src_dir, full_metadata_dir):
    if not os.path.exists(full_src_dir):
        logger.error(f"Dir does not exist: {full_src_dir}")
        exit(3)

    if os.path.exists(f'{full_metadata_dir}/vocabsize'):
        logger.warning(f"File already exists: {full_metadata_dir}/vocabsize. Doing nothing.")
        exit(0)

    logger.info(f"Reading files from: {os.path.abspath(full_src_dir)}")

    all_files = get_all_files(full_src_dir, REPR_EXTENSION)
    if not all_files:
        logger.warning("No preprocessed files found.")
        exit(4)

    path_to_dump = f'{full_metadata_dir}/part_vocab/'
    dumps_valid_file = f'{path_to_dump}/ready'

    if os.path.exists(dumps_valid_file):
        all_files = get_all_files(path_to_dump, PARTVOCAB_EXT)
        task_list = []
        for file in all_files:
            if '_' in os.path.basename(file):  # not very robust solution for checking if creation of this backup file
                # hasn't been terminated properly
                file = finish_file_dumping(file)
            task_list.append(pickle.load(open(file, 'rb')))

        logger.info(f"Loaded partially calculated vocabs from {path_to_dump}")
    else:
        logger.info(f"Starting merging from scratch")
        if os.path.exists(path_to_dump):
            shutil.rmtree(path_to_dump)
        os.makedirs(path_to_dump)
        task_list = create_initial_partial_vocabs(all_files)
        for partial_vocab in task_list:
            pickle.dump(partial_vocab, open(f'{path_to_dump}/{partial_vocab.id}.{PARTVOCAB_EXT}', 'wb'))
        open(dumps_valid_file, 'a').close()

    task_queue = list_to_queue(task_list)

    num_mergers = multiprocessing.cpu_count()
    logger.info(f"Using {num_mergers} mergers")
    mergers = [Merger(task_queue, path_to_dump) for i in range(num_mergers)]
    for merger in mergers:
        merger.start()
    count = 1
    for merger in mergers:
        logger.debug(f"Waiting for merger {count}/{num_mergers} to join")
        count += 1
        merger.join()

    final_vocab = task_queue.get_nowait()
    try:
        task_queue.get_nowait()
        raise AssertionError()
    except:
        pass

    final_vocab.write_stats(f'{full_metadata_dir}/vocabsize')
    final_vocab.write_vocab(f'{full_metadata_dir}/vocab')
    shutil.rmtree(path_to_dump)
    # time.sleep(1)


def list_to_queue(lst):
    queue = multiprocessing.Queue()
    for elm in lst:
        queue.put_nowait(elm)
    return queue


def create_initial_partial_vocabs(all_files):
    partial_vocabs_queue = []
    files_total = len(all_files)
    current_file = 0
    start_time = time.time()
    with Pool() as pool:
        it = pool.imap_unordered(get_vocab, all_files)
        for vocab in it:
            partial_vocab = PartialVocab(vocab)
            partial_vocabs_queue.append(partial_vocab)
            current_file += 1
            logger.info(f"To partial vocabs added  {current_file} out of {files_total}")
            time_elapsed = time.time() - start_time
            logger.info(f"Time elapsed: {time_elapsed:.2f} s, estimated time until completion: "
                        f"{time_elapsed / current_file * files_total - time_elapsed:.2f} s")
    return partial_vocabs_queue


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--base-from', action='store', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('dataset', action='store', help=f'dataset name')
    parser.add_argument('repr', action='store', help=f'repr name')

    args = parser.parse_known_args(*DEFAULT_VOCABSIZE_ARGS)
    args = args[0]

    full_src_dir = f'{args.base_from}/{args.dataset}/repr/{args.repr}/train'
    full_metadata_dir = f'{args.base_from}/{args.dataset}/metadata/{args.repr}'

    run(full_src_dir, full_metadata_dir)
