import argparse
import logging.config
import multiprocessing
import os
import sys
from multiprocessing import Queue
from queue import Empty
from typing import List, Tuple, Dict

import dill as pickle
import shutil
import time
from collections import Counter, defaultdict
from multiprocessing.pool import Pool

from torchtext.data import Field
from tqdm import tqdm

from logrec.dataprep import TRAIN_DIR, METADATA_DIR, REPR_DIR, TEXT_FIELD_FILE
from logrec.dataprep.model.placeholders import placeholders
from logrec.dataprep.parse_projects import read_file_contents
from logrec.dataprep.to_repr import REPR_EXTENSION
from logrec.dataprep.util import AtomicInteger, merge_dicts_
from logrec.infrastructure import fractions_manager
from logrec.util import io
from logrec.util.files import file_mapper

logger = logging.getLogger(__name__)

queue_size = AtomicInteger()

PARTVOCAB_EXT = 'partvocab'
VOCABSIZE_FILENAME = 'vocabsize'
VOCAB_FILENAME = 'vocab'

N_CHUNKS = 20
BLOCKING_TIMEOUT_SECONDS_SHORT = 5
BLOCKING_TIMEOUT_SECONDS_LONG = 300


class PartialVocab(object):
    CLASS_VERSION = '2.0.0'

    def __init__(self, word_counts: Counter, chunk: int):
        if not isinstance(word_counts, Counter):
            raise TypeError(f'Vocab must be a Counter, but is {type(word_counts)}')

        self.merged_word_counts = word_counts
        self.stats = [(1,
                       len(self.merged_word_counts),
                       self.merged_word_counts[placeholders['non_eng']],
                       self.merged_word_counts[placeholders['non_eng_content']])]
        self.n_files = 1
        self.chunk = chunk
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        return str(os.getpid()) + ''.join(str(time.time()).split('.'))

    def renew_id(self) -> None:
        self.id = self._generate_id()

    def set_path_to_dump(self, path) -> None:
        self.path_to_dump = path

    def add_vocab(self, partial_vocab: 'PartialVocab') -> List[str]:
        self.merged_word_counts, new_words = merge_dicts_(self.merged_word_counts, partial_vocab.merged_word_counts)
        cur_vocab_size = len(self.merged_word_counts)

        self.n_files += partial_vocab.n_files
        new_stats_entry = (self.n_files,
                           cur_vocab_size,
                           self.merged_word_counts[placeholders['non_eng']],
                           self.merged_word_counts[placeholders['non_eng_content']])
        self.stats.extend(partial_vocab.stats + [new_stats_entry])
        return new_words

    def write_stats(self, path_to_stats_file: str) -> None:
        stats = self.__generate_stats()
        with open(path_to_stats_file, 'w') as f:
            vocabsize = int(stats[-1][1][0])
            f.write(f'{vocabsize}\n')
            for percent, (v, n, nn) in stats:
                f.write(f"{percent:.4f} {int(v)} {int(n)} {int(nn)}\n")

    def limit_max_vocab(self, vocab_size_threshold: int):
        sorted_vocab = sorted(self.merged_word_counts.items(), key=lambda x: x[1], reverse=True)
        if vocab_size_threshold > len(sorted_vocab):
            return
        min_freq_excluded = sorted_vocab[vocab_size_threshold][1]
        adjusted_threshold = vocab_size_threshold - 1
        while adjusted_threshold >= 0 and sorted_vocab[adjusted_threshold][1] == min_freq_excluded:
            adjusted_threshold -= 1
        self.merged_word_counts = {k: v for (k, v) in sorted_vocab[:adjusted_threshold + 1]}

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
            d[entry[0]].append(tuple(entry[1:]))
        fin = {(float(k) / self.n_files): tuple([sum(elm) / len(elm) for elm in zip(*v)]) for k, v in d.items()}
        return sorted(fin.items())


class VocabMerger(multiprocessing.Process):
    def __init__(self, id: int, tasks: Dict[int, Queue], path_to_dump: str, process_counter: AtomicInteger,
                 chunk_queue: Queue, merges_left_counter: AtomicInteger, max_vocab_threshold: int,
                 prefix: str):
        multiprocessing.Process.__init__(self)
        self.id = id
        self.tasks = tasks
        self.path_to_dump = path_to_dump
        self.process_counter = process_counter
        self.chunk_queue = chunk_queue
        self.merges_left_counter = merges_left_counter
        self.total_merges = merges_left_counter.value
        self.max_vocab_threshold = max_vocab_threshold
        self.prefix = prefix


    def run(self):
        while True:
            chunk_assigned = self.chunk_queue.get(block=True, timeout=BLOCKING_TIMEOUT_SECONDS_SHORT)
            if chunk_assigned == -1:
                if not self.process_counter.compare_and_dec(1):
                    logger.debug(
                        f"[{self.id}] No vocabs available for merge. "
                        f"Terminating process..., mergers left: {self.process_counter.value}")
                    break
                else:
                    logger.info("Leaving 1 process to finish the merges")
                    self._finish_merges()
                    logger.info(f'[{self.id}] Vocab files are saved. Terminating the process...')
                    break

            first = None
            try:
                first = self.tasks[chunk_assigned].get(block=True, timeout=BLOCKING_TIMEOUT_SECONDS_LONG)
                second = self.tasks[chunk_assigned].get(block=True, timeout=BLOCKING_TIMEOUT_SECONDS_LONG)
            except Empty:
                logger.debug(f"[{self.id}] Could not get a task from queue. Terminating")
                if first:
                    self.tasks[chunk_assigned].put_nowait(first)
                return

            start = time.time()

            merges_left = self.merges_left_counter.get_and_dec()
            merges_done = self.total_merges - merges_left
            log_this_merge = (merges_left & (merges_left - 1) == 0 or merges_done & (merges_done - 1) == 0)
            if log_this_merge:
                logger.info(
                    f'[{self.id}] Merging vocabs ({self.total_merges - merges_left} out of {self.total_merges})')

            first, new_words = self._merge(first, second)

            if log_this_merge:
                self._log_merge_results(new_words, len(first.merged_word_counts), time.time() - start)

            self.tasks[chunk_assigned].put_nowait(first)

    def _finish_merges(self):
        logger.info("===============     Finishing merges    ===============")
        list_from_chunks = [queue.get(block=True, timeout=BLOCKING_TIMEOUT_SECONDS_SHORT) for queue in
                            self.tasks.values()]

        percents_in_one_chunk = 100 // len(list_from_chunks)

        first = list_from_chunks.pop()
        for i, vocab in enumerate(list_from_chunks):
            logger.info(
                f'{(i+1)* percents_in_one_chunk}% + {percents_in_one_chunk}%  ---> {(i+2) * percents_in_one_chunk}%')

            start = time.time()

            first, new_words = self._merge(first, vocab)

            self._log_merge_results(new_words, len(first.merged_word_counts), time.time() - start)

        first.limit_max_vocab(self.max_vocab_threshold)

        first.write_stats(os.path.join(full_metadata_dir, f'{self.prefix}{VOCABSIZE_FILENAME}'))
        first.write_vocab(os.path.join(full_metadata_dir, f'{self.prefix}{VOCAB_FILENAME}'))
        first.write_field(os.path.join(full_metadata_dir, f'{self.prefix}{TEXT_FIELD_FILE}'))
        shutil.rmtree(self.path_to_dump)

    def _log_merge_results(self, new_words: List[str], resulting_vocab_size: int, time: float):
        logger.debug(f"[{self.id}] New words: {new_words[:10]} ..., total: {len(new_words)}")
        logger.info(
            f"[{self.id}] Merging took {time:.3f} s, current vocab size: {resulting_vocab_size}")

    def _merge(self, first: PartialVocab, second: PartialVocab) -> Tuple[PartialVocab, List[str]]:
        first_id = first.id
        second_id = second.id

        new_words = first.add_vocab(second)

        first.renew_id()
        path_to_new_file = os.path.join(self.path_to_dump, f'{first_id}_{second_id}_{first.id}.{PARTVOCAB_EXT}')
        pickle.dump(first, open(path_to_new_file, 'wb'))
        finish_file_dumping(path_to_new_file)

        return first, new_words


def get_vocab(path_to_file: str) -> Counter:
    vocab = Counter()
    lines, _ = read_file_contents(path_to_file)
    for line in lines:
        vocab.update(line.rstrip('\n').split(' '))
    return vocab


def create_and_dump_partial_vocab(param):
    path_to_file, path_to_dump, chunk = param
    vocab = get_vocab(path_to_file)
    partial_vocab = PartialVocab(vocab, chunk)
    pickle.dump(partial_vocab, open(os.path.join(path_to_dump, f'{partial_vocab.id}.{PARTVOCAB_EXT}'), 'wb'))
    return partial_vocab


def finish_file_dumping(path_to_new_file):
    try:
        pickle.load(open(path_to_new_file, 'rb'))
    except EOFError:
        # file has not been written properly
        os.remove(path_to_new_file)
        return

    dir, base = os.path.split(path_to_new_file)
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
    chunk_generator = create_chunk_generator(len(all_files), N_CHUNKS)
    params = [(file, path_to_dump, chunk) for file, chunk in zip(all_files, chunk_generator)]
    pool = Pool()
    partial_vocab_it = pool.imap_unordered(create_and_dump_partial_vocab, params)
    for partial_vocab in tqdm(partial_vocab_it, total=files_total):
        partial_vocabs_queue.append(partial_vocab)
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


def file_generator(full_src_dir, percent, start_from):
    return file_mapper(full_src_dir,
                       lambda l: l, lambda fi: fi.endswith(REPR_EXTENSION)
                                               and fractions_manager.included_in_fraction(fi, percent, start_from))

def run(full_src_dir: str, full_metadata_dir: str, max_vocab_threshold: int, percent: float, start_from: float):
    prefix = fractions_manager.get_percent_prefix(percent, start_from)
    prefix = '' if prefix == '100_' else prefix

    if not os.path.exists(full_src_dir):
        logger.error(f"Dir does not exist: {full_src_dir}")
        exit(3)

    if os.path.exists(os.path.join(full_metadata_dir, f'{prefix}{VOCABSIZE_FILENAME}')):
        logger.warning(f"File already exists: {os.path.join(full_metadata_dir, f'{prefix}{VOCABSIZE_FILENAME}')}. Doing nothing.")
        exit(0)

    logger.info(f"Reading files from: {os.path.abspath(full_src_dir)}")

    all_files = [file for file in file_generator(full_src_dir, percent, start_from)]
    if not all_files:
        logger.warning("No preprocessed files found.")
        exit(4)

    path_to_dump = os.path.join(full_metadata_dir, 'part_vocab')
    dumps_valid_file = os.path.join(path_to_dump, 'ready')

    if os.path.exists(dumps_valid_file):
        for file in file_generator(full_src_dir, percent, start_from):
            if '_' in os.path.basename(file):  # not very robust solution for checking if creation of this backup file
                # hasn't been terminated properly
                finish_file_dumping(file)

        task_list = []
        for file in file_generator(full_src_dir, percent, start_from):
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

    n_processes = multiprocessing.cpu_count()
    logger.info(f"Using {n_processes} mergers, number of partial vocabs: {len(task_list)}")
    tasks_queues, chunk_sizes = mapify_tasks(task_list)
    chunk_queue, merges_to_be_done = create_chunk_queue(chunk_sizes, n_processes)
    logger.info(f'==================    Starting merging    =================')
    logger.info(f'Merges need to be done: {merges_to_be_done}')
    process_counter = AtomicInteger(n_processes)
    merges_left_counter = AtomicInteger(merges_to_be_done)
    mergers = [VocabMerger(i + 1, tasks_queues, path_to_dump, process_counter, chunk_queue,
                           merges_left_counter, max_vocab_threshold, prefix)
               for i in range(n_processes)]
    for merger in mergers:
        merger.start()


if __name__ == '__main__':
    from logrec.properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_VOCABSIZE_ARGS

    parser = argparse.ArgumentParser()
    parser.add_argument('--base-from', action='store', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('dataset', action='store', help=f'dataset name')
    parser.add_argument('repr', action='store', help=f'repr name')
    parser.add_argument('--max-vocab-threshold', action='store', type=int, default=sys.maxsize)
    parser.add_argument('--percent', action='store', type=float, default=100.0)
    parser.add_argument('--start-from', action='store', type=float, default=0.0)

    args = parser.parse_known_args(*DEFAULT_VOCABSIZE_ARGS)
    args = args[0]

    path_to_dataset = os.path.join(args.base_from, args.dataset)
    full_src_dir = os.path.join(path_to_dataset, REPR_DIR, args.repr, TRAIN_DIR)
    full_metadata_dir = os.path.join(path_to_dataset, METADATA_DIR, args.repr)

    run(full_src_dir, full_metadata_dir, args.max_vocab_threshold, args.percent, args.start_from)
