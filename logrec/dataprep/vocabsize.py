import argparse
import logging.config
import multiprocessing
import os
from multiprocessing import Queue
from typing import List, Tuple, Dict

import dill as pickle
import shutil
import time
from collections import Counter, defaultdict
from multiprocessing.pool import Pool

from torchtext.data import Field

from logrec.dataprep import TRAIN_DIR, METADATA_DIR, REPR_DIR, TEXT_FIELD_FILE
from logrec.dataprep.model.placeholders import placeholders
from logrec.dataprep.to_repr import REPR_EXTENSION
from logrec.dataprep.util import AtomicInteger, merge_dicts_
from logrec.util import io
from logrec.util.files import file_mapper

logger = logging.getLogger(__name__)

queue_size = AtomicInteger()

PARTVOCAB_EXT = 'partvocab'
VOCABSIZE_FILENAME = 'vocabsize'
VOCAB_FILENAME = 'vocab'

N_CHUNKS = 1
BLOCKING_TIMEOUT_SECONDS = 5


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

    def add_vocab(self, partial_vocab) -> List[str]:
        if not isinstance(partial_vocab, PartialVocab):
            raise TypeError(f'Vocab must be a PartialVocab, but is {type(partial_vocab)}')

        self.merged_word_counts, new_words = merge_dicts_(self.merged_word_counts, partial_vocab.merged_word_counts)
        cur_vocab_size = len(self.merged_word_counts)

        self.n_files += partial_vocab.n_files
        new_stats_entry = (self.n_files, cur_vocab_size, self.merged_word_counts[placeholders['non_eng']])
        self.stats.extend(partial_vocab.stats + [new_stats_entry])
        return new_words

    def write_stats(self, path_to_stats_file: str) -> None:
        stats = self.__generate_stats()
        with open(path_to_stats_file, 'w') as f:
            vocabsize = int(stats[-1][1][0])
            f.write(f'{vocabsize}\n')
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
    def __init__(self, id: int, tasks: Dict[int, Queue], path_to_dump: str, process_counter: AtomicInteger,
                 chunk_queue: Queue, chunk_queue_elm_counter: AtomicInteger):
        multiprocessing.Process.__init__(self)
        self.id = id
        self.tasks = tasks
        self.path_to_dump = path_to_dump
        self.process_counter = process_counter
        self.chunk_queue = chunk_queue
        self.chunk_queue_elm_counter = chunk_queue_elm_counter
        self.total_merges = chunk_queue_elm_counter.value

    def run(self):
        while True:
            chunk_assigned = self.chunk_queue.get(block=True, timeout=BLOCKING_TIMEOUT_SECONDS)
            if chunk_assigned == -1:
                if not self.process_counter.compare_and_dec(1):
                    logger.debug(
                        f"[{self.id}] No vocabs available for merge. "
                        f"Terminating process..., mergers left: {self.process_counter.value}")
                    break
                else:
                    logger.info("Leaving 1 process to finish the merges")
                    self.__finish_merges()
                    logger.info(f'[{self.id}] Vocab files are saved. Terminating the process...')
                    break

            first = self.tasks[chunk_assigned].get(block=True, timeout=BLOCKING_TIMEOUT_SECONDS)
            second = self.tasks[chunk_assigned].get(block=True, timeout=BLOCKING_TIMEOUT_SECONDS)

            start = time.time()

            merges_left = self.chunk_queue_elm_counter.get_and_dec()
            merges_done = self.total_merges - merges_left
            log_this_merge = (merges_left & (merges_left - 1) == 0 or merges_done & (merges_done - 1) == 0)
            if log_this_merge:
                logger.info(
                    f'[{self.id}] Merging vocabs ({self.total_merges - merges_left} out of {self.total_merges})')

            first, new_words = self.__merge_(first, second)

            if log_this_merge:
                self.__log_merge_results(new_words, len(first.merged_word_counts), time.time() - start)

            self.tasks[chunk_assigned].put_nowait(first)

    def __finish_merges(self):
        logger.info("===============     Finishing merges    ===============")
        list_from_chunks = [queue.get(block=True, timeout=BLOCKING_TIMEOUT_SECONDS) for queue in self.tasks.values()]

        percents_in_one_chunk = 100 // len(list_from_chunks)

        first = list_from_chunks.pop()
        for i, vocab in enumerate(list_from_chunks):
            logger.info(
                f'{(i+1)* percents_in_one_chunk}% + {percents_in_one_chunk}%  ---> {(i+2) * percents_in_one_chunk}%')

            start = time.time()

            first, new_words = self.__merge_(first, vocab)

            self.__log_merge_results(new_words, len(first.merged_word_counts), time.time() - start)

        first.write_stats(os.path.join(full_metadata_dir, VOCABSIZE_FILENAME))
        first.write_vocab(os.path.join(full_metadata_dir, VOCAB_FILENAME))
        first.write_field(os.path.join(full_metadata_dir, TEXT_FIELD_FILE))
        shutil.rmtree(self.path_to_dump)

    def __log_merge_results(self, new_words: List[str], resulting_vocab_size: int, time: float):
        logger.debug(f"[{self.id}] New words: {new_words[:10]} ..., total: {len(new_words)}")
        logger.info(
            f"[{self.id}] Merging took {time:.3f} s, current vocab size: {resulting_vocab_size}")

    def __merge_(self, first: PartialVocab, second: PartialVocab) -> Tuple[PartialVocab, List[str]]:
        first_id = first.id
        second_id = second.id

        new_words = first.add_vocab(second)

        first.renew_id()
        path_to_new_file = os.path.join(self.path_to_dump, f'{first_id}_{second_id}_{first.id}.{PARTVOCAB_EXT}')
        pickle.dump(first, open(path_to_new_file, 'wb'))
        finish_file_dumping(path_to_new_file)

        return first, new_words


# TODO remove this ugliness!!
def avg_ssum(nested_list):
    sm = (0, 0)
    for i, k in nested_list:
        sm = (sm[0] + i, sm[1] + k)
    return (sm[0] / float(len(nested_list)), sm[1] / float(len(nested_list)))


def get_vocab(path_to_file: str) -> Counter:
    vocab = Counter()
    with open(path_to_file, 'r') as f:
        for line in f:
            if line[-1] == '\n':
                line = line[:-1]
            split = line.split(' ')
            vocab.update(split)
    return vocab


def create_and_dump_partial_vocab(param):
    path_to_file, path_to_dump, chunk = param
    vocab = get_vocab(path_to_file)
    partial_vocab = PartialVocab(vocab, chunk)
    pickle.dump(partial_vocab, open(os.path.join(path_to_dump, f'{partial_vocab.id}.{PARTVOCAB_EXT}'), 'wb'))
    return partial_vocab


def finish_file_dumping(path_to_new_file):
    base = os.path.basename(path_to_new_file)
    dir = os.path.dirname(path_to_new_file)
    spl = base.split('.')[0].split('_')
    if len(spl) != 3:
        raise AssertionError(f'Wrong file: {path_to_new_file}')
    first_id, second_id, new_id = spl[0], spl[1], spl[2]

    first_file = os.path.join(dir, f'{first_id}.{PARTVOCAB_EXT}')
    if os.path.exists(first_file):
        os.remove(first_file)

    second_file = os.path.join(dir, f'{second_id}.{PARTVOCAB_EXT}')
    if os.path.exists(second_file):
        os.remove(second_file)

    new_file = os.path.join(dir, f'{new_id}.{PARTVOCAB_EXT}')
    os.rename(path_to_new_file, new_file)
    return new_file, (first_file, second_file)


def list_to_queue(lst: List) -> Queue:
    queue = Queue()
    for elm in lst:
        queue.put_nowait(elm)
    return queue


def create_chunk_generator(total: int, n_chunks: int):
    min_elms_in_chunk = total // n_chunks
    for i in range(min_elms_in_chunk):
        for j in range(n_chunks):
            yield j
    for i in range(total % n_chunks):
        yield i


def create_initial_partial_vocabs(all_files, path_to_dump: str):
    partial_vocabs_queue = []
    files_total = len(all_files)
    current_file = 0
    chunk_generator = create_chunk_generator(len(all_files), N_CHUNKS)
    params = [(file, path_to_dump, chunk) for file, chunk in zip(all_files, chunk_generator)]
    pool = Pool()
    partial_vocab_it = pool.imap_unordered(create_and_dump_partial_vocab, params)
    for partial_vocab in partial_vocab_it:
        partial_vocabs_queue.append(partial_vocab)
        current_file += 1
        logger.info(f"To partial vocabs added  {current_file} out of {files_total}")
    pool.terminate()
    return partial_vocabs_queue


def create_chunk_queue(chunk_sizes: Dict[int, int], num_mergers: int) -> Tuple[Queue, int]:
    chunk_queue_list = [chunk for chunk, chunk_size in chunk_sizes.items() for _ in range(chunk_size - 1)]
    return list_to_queue(chunk_queue_list + [-1 for _ in range(num_mergers)]), len(chunk_queue_list)


def mapify_tasks(tasks: List[PartialVocab]) -> Tuple[Dict[int, Queue], Dict[int, int]]:
    task_lists_in_chunks = defaultdict(list)
    for task in tasks:
        task_lists_in_chunks[task.chunk].append(task)
    return {chunk: list_to_queue(task_list_in_chunk) for chunk, task_list_in_chunk in
            task_lists_in_chunks.items()}, {k: len(v) for k, v in task_lists_in_chunks.items()}


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
        logger.info(f"Calculating vocabulary from scratch")
        if os.path.exists(path_to_dump):
            shutil.rmtree(path_to_dump)
        os.makedirs(path_to_dump)
        task_list = create_initial_partial_vocabs(all_files, path_to_dump)
        open(dumps_valid_file, 'a').close()

    num_mergers = multiprocessing.cpu_count()
    logger.info(f"Using {num_mergers} mergers, number of partial vocabs: {len(task_list)}")
    queue_size.value = len(task_list)
    merger_counter = AtomicInteger(num_mergers)
    tasks_queues, chunk_sizes = mapify_tasks(task_list)
    chunk_queue, chunk_queue_size = create_chunk_queue(chunk_sizes, num_mergers)
    logger.info(f'==================    Starting merging    =================')
    logger.info(f'Merges need to be done: {chunk_queue_size}')
    chunk_queue_elm_counter = AtomicInteger(chunk_queue_size)
    mergers = [VocabMerger(i + 1, tasks_queues, path_to_dump, merger_counter, chunk_queue, chunk_queue_elm_counter) for
               i in range(num_mergers)]
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
    logger.info("Terminating parent process ... ")
