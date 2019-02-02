import argparse
import logging.config
import multiprocessing
import os
from typing import List, Tuple, Dict

import dill as pickle
import queue
import random
import shutil
import time
from collections import Counter, defaultdict
from multiprocessing.pool import Pool

import yaml
from torchtext.data import Field

from logrec.dataprep import base_project_dir, TRAIN_DIR, METADATA_DIR, REPR_DIR, TEXT_FIELD_FILE
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.to_repr import REPR_EXTENSION
from logrec.dataprep.util import AtomicInteger, merge_dicts_
from logrec.util import io
from logrec.util.files import file_mapper

logger = logging.getLogger(__name__)

queue_size = AtomicInteger()

PARTVOCAB_EXT = 'partvocab'

N_CHUNKS = 20


class PartialVocab(object):
    CLASS_VERSION = '2.0.0'

    def __init__(self, word_counts: Counter, chunk: int):
        if not isinstance(word_counts, Counter):
            raise TypeError(f'Vocab must be a Counter, but is {type(word_counts)}')

        self.merged_word_counts = word_counts
        self.stats = [(1, len(self.merged_word_counts), self.merged_word_counts[placeholders['non_eng']])]
        self.n_files = 1
        self.chunk = chunk
        self.id = self.__generate_id()

    def __generate_id(self) -> str:
        return ''.join(str(time.time()).split('.'))

    def renew_id(self) -> None:
        self.id = self.__generate_id()

    def set_path_to_dump(self, path) -> None:
        self.path_to_dump = path

    def add_vocab(self, partial_vocab) -> None:
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

    def write_stats(self, path_to_stats_file: str) -> None:
        stats = self.__generate_stats()
        with open(path_to_stats_file, 'w') as f:
            vocabsize = int(stats[-1][1][0])
            f.write(f"{str(vocabsize)}\n")
            for percent, (v, n) in stats:
                f.write(f"{percent} {v} {n}\n")

    def write_vocab(self, path_to_vocab_file: str) -> None:
        sorted_vocab = sorted(self.merged_word_counts.items(), key=lambda x: x[1], reverse=True)
        io.dump_dict_into_2_columns(sorted_vocab, path_to_vocab_file)

    def write_field(self, path_to_field_file: str) -> None:
        text_field = Field(tokenize=lambda s: s.split(" "), pad_token=placeholders['pad_token'])
        text_field.build_vocab([[i] for i in self.merged_word_counts.keys()])
        pickle.dump(text_field, open(path_to_field_file, 'wb'))

    def __generate_stats(self):
        d = defaultdict(list)
        for entry in self.stats:
            d[entry[0]].append((entry[1], entry[2]))
        fin = {(float(k) / self.n_files): avg_ssum(v) for k, v in d.items()}
        return sorted(fin.items())


class VocabMerger(multiprocessing.Process):
    def __init__(self, id: int, tasks: List[PartialVocab], path_to_dump: str, process_counter: AtomicInteger):
        multiprocessing.Process.__init__(self)
        self.id = id
        self.tasks, chunk_sizes = VocabMerger.__mapify_tasks(tasks)
        self.path_to_dump = path_to_dump
        self.process_counter = process_counter
        self.chunk_queue, size = VocabMerger.__create_chunk_queue(chunk_sizes)
        self.total_merges_to_be_done = size
        logger.info(f'Merges need to be done: {self.total_merges_to_be_done}')

    def run(self):
        while True:
            try:
                chunk_assigned = self.chunk_queue.get(block=False)
            except queue.Empty:
                if not self.process_counter.compare_and_dec(1):
                    logger.debug(
                        f"[{self.id}] No vocabs available for merge. Terminating process..., mergers left: {self.process_counter.value}")
                    break
                else:
                    logger.info("Leaving 1 process to finish the merges")
                    self.__finish_merges()
                    break

            logger.debug("Doing merge ...")
            first = self.tasks[chunk_assigned].get(block=True)
            second = self.tasks[chunk_assigned].get(block=True)

            self.__merge(first, second, self.tasks[chunk_assigned])

    @staticmethod
    def __create_chunk_queue(chunk_sizes: Dict[int, int]) -> Tuple[multiprocessing.Queue, int]:
        chunk_queue_list = [chunk for chunk, chunk_size in chunk_sizes.items() for _ in range(chunk_size - 1)]
        return list_to_queue(chunk_queue_list), len(chunk_queue_list)

    @staticmethod
    def __mapify_tasks(tasks: List[PartialVocab]) -> Tuple[Dict[int, multiprocessing.Queue], Dict[int, int]]:
        task_lists_in_chunks = defaultdict(list)
        for task in tasks:
            task_lists_in_chunks[task.chunk].append(task)
        return {chunk: list_to_queue(task_list_in_chunk) for chunk, task_list_in_chunk in
                task_lists_in_chunks.items()}, {k: len(v) for k, v in task_lists_in_chunks.items()}

    def __finish_merges(self):
        logger.info("Finishing merges")
        list_from_chunks_list = [queue.get_nowait() for queue in self.tasks.values()]
        print(len(list_from_chunks_list))
        queue_from_chunks = list_to_queue(list_from_chunks_list)
        merges_left = len(list_from_chunks_list) - 1
        for i in range(merges_left):
            logger.debug(f'{i+1} / {merges_left}')
            first = queue_from_chunks.get(block=True)
            second = queue_from_chunks.get(block=True)
            self.__merge(first, second, queue_from_chunks)
        final_vocab = queue_from_chunks.get(block=True)

        final_vocab.write_stats(os.path.join(full_metadata_dir, 'vocabsize'))
        final_vocab.write_vocab(os.path.join(full_metadata_dir, 'vocab'))
        final_vocab.write_field(os.path.join(full_metadata_dir, TEXT_FIELD_FILE))
        shutil.rmtree(self.path_to_dump)

    def __merge(self, first: PartialVocab, second: PartialVocab, queue_to_return_to: multiprocessing.Queue):
        first_id = first.id
        second_id = second.id

        first.add_vocab(second)

        first.renew_id()
        path_to_new_file = os.path.join(self.path_to_dump, f'{first_id}_{second_id}_{first.id}.{PARTVOCAB_EXT}')
        pickle.dump(first, open(path_to_new_file, 'wb'))
        finish_file_dumping(path_to_new_file)

        queue_to_return_to.put_nowait(first)
        logger.debug("Put to queue")


# TODO remove this ugliness!!
def avg_ssum(nested_list):
    sm = (0, 0)
    for i, k in nested_list:
        sm = (sm[0] + i, sm[1] + k)
    return (sm[0] / float(len(nested_list)), sm[1] / float(len(nested_list)))


def get_vocab(path_to_file):
    vocab = Counter()
    with open(path_to_file, 'r') as f:
        for line in f:
            if line[-1] == '\n':
                line = line[:-1]
            split = line.split(' ')
            vocab.update(split)
    return vocab


def finish_file_dumping(path_to_new_file):
    base = os.path.basename(path_to_new_file)
    dir = os.path.dirname(path_to_new_file)
    spl = base.split('.')[0].split('_')
    if len(spl) != 3:
        raise AssertionError(f'Wrong file: {path_to_new_file}')
    first_id, second_id, new_id = spl[0], spl[1], spl[2]

    first_file = os.path.join(dir, f'{first_id}.{PARTVOCAB_EXT}')
    logger.debug(f'Removing if doesnt exist: {first_file}')
    if os.path.exists(first_file):
        os.remove(first_file)

    second_file = os.path.join(dir, f'{second_id}.{PARTVOCAB_EXT}')
    logger.debug(f'Removing if doesnt exist: {second_file}')
    if os.path.exists(second_file):
        os.remove(second_file)

    new_file = os.path.join(dir, f'{new_id}.{PARTVOCAB_EXT}')
    os.rename(path_to_new_file, new_file)
    logger.debug(f'Renaming {path_to_new_file} --> {new_file}')
    return new_file, (first_file, second_file)


def list_to_queue(lst: List) -> multiprocessing.Queue:
    queue = multiprocessing.Queue()
    for elm in lst:
        queue.put_nowait(elm)
    return queue


def chunk_generator(total: int, n_chunks: int):
    min_elms_in_chunk = total // n_chunks
    for i in range(min_elms_in_chunk):
        for j in range(n_chunks):
            yield j
    for i in range(total % n_chunks):
        yield i


def create_initial_partial_vocabs(all_files):
    partial_vocabs_queue = []
    files_total = len(all_files)
    current_file = 0
    start_time = time.time()
    with Pool() as pool:
        words_from_one_file_freqs_it = pool.imap_unordered(get_vocab, all_files)
        for words_from_one_file_freqs, chunk in zip(words_from_one_file_freqs_it,
                                                    chunk_generator(len(all_files), N_CHUNKS)):
            partial_vocab = PartialVocab(words_from_one_file_freqs, chunk)
            partial_vocabs_queue.append(partial_vocab)
            current_file += 1
            logger.info(f"To partial vocabs added  {current_file} out of {files_total}")
            time_elapsed = time.time() - start_time
            logger.info(f"Time elapsed: {time_elapsed:.2f} s, estimated time until completion: "
                        f"{time_elapsed / current_file * files_total - time_elapsed:.2f} s")
    return partial_vocabs_queue


def run(full_src_dir, full_metadata_dir):
    if not os.path.exists(full_src_dir):
        logger.error(f"Dir does not exist: {full_src_dir}")
        exit(3)

    if os.path.exists(os.path.join(full_metadata_dir, 'vocabsize')):
        logger.warning(f"File already exists: {os.path.join(full_metadata_dir, 'vocabsize')}. Doing nothing.")
        exit(0)

    logger.info(f"Reading files from: {os.path.abspath(full_src_dir)}")

    all_files = [file for file in file_mapper(full_src_dir, lambda l: l, REPR_EXTENSION)]
    if not all_files:
        logger.warning("No preprocessed files found.")
        exit(4)

    path_to_dump = os.path.join(full_metadata_dir, 'part_vocab')
    dumps_valid_file = os.path.join(path_to_dump, 'ready')

    if os.path.exists(dumps_valid_file):
        all_files = [file for file in file_mapper(path_to_dump, lambda l: l, PARTVOCAB_EXT)]
        task_list = []
        removed_files = []
        for file in all_files:
            if '_' in os.path.basename(file):  # not very robust solution for checking if creation of this backup file
                # hasn't been terminated properly
                file, rm_files = finish_file_dumping(file)
                removed_files.extend(list(rm_files))
            if file not in removed_files:
                part_vocab = pickle.load(open(file, 'rb'))
                if not isinstance(part_vocab, PartialVocab):
                    raise TypeError(f"Object {str(part_vocab)} must be VocabMerger version {part_vocab.VERSION}")
                task_list.append(part_vocab)

        logger.info(f"Loaded partially calculated vocabs from {path_to_dump}")
    else:
        logger.info(f"Starting merging from scratch")
        if os.path.exists(path_to_dump):
            shutil.rmtree(path_to_dump)
        os.makedirs(path_to_dump)
        task_list = create_initial_partial_vocabs(all_files)
        for partial_vocab in task_list:
            pickle.dump(partial_vocab, open(os.path.join(path_to_dump, f'{partial_vocab.id}.{PARTVOCAB_EXT}'), 'wb'))
        open(dumps_valid_file, 'a').close()

    num_mergers = multiprocessing.cpu_count()
    logger.info(f"Using {num_mergers} mergers, number of partial vocabs: {len(task_list)}")
    queue_size.value = len(task_list)
    merger_counter = AtomicInteger(num_mergers)
    mergers = [VocabMerger(i + 1, task_list, path_to_dump, merger_counter) for i in range(num_mergers)]
    for merger in mergers:
        merger.start()

if __name__ == '__main__':
    from logrec.properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_VOCABSIZE_ARGS

    parser = argparse.ArgumentParser()
    parser.add_argument('--base-from', action='store', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('dataset', action='store', help=f'dataset name')
    parser.add_argument('repr', action='store', help=f'repr name')

    args = parser.parse_known_args(*DEFAULT_VOCABSIZE_ARGS)
    args = args[0]

    path_to_dataset = os.path.join(args.base_from, args.dataset)
    full_src_dir = os.path.join(path_to_dataset, REPR_DIR, args.repr, TRAIN_DIR)
    full_metadata_dir = os.path.join(path_to_dataset, METADATA_DIR, args.repr)

    run(full_src_dir, full_metadata_dir)
