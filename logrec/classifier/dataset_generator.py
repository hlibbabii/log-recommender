import argparse
import logging
import os
import random
import re
from typing import List, Tuple, Callable

CLASSIFICATION_TYPE = 'location'

from logrec.classifier.context_datasets import ContextsDataset, get_dir_and_file, WORDS_IN_CONTEXT_LIMIT
from logrec.dataprep import REPR_DIR, TRAIN_DIR, TEST_DIR, VALID_DIR
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.preprocessors.preprocessing_types import PrepParamsParser
from logrec.infrastructure.fs import CLASSIFICATION_DIR_NAME
from logrec.util.io_utils import file_mapper


logger = logging.getLogger(__name__)


def create_side_of_case(
        list_of_words: list,
        position: int,
        end: int,
        step: Callable[[int], int],
        can_iterate: Callable[[int, int], bool],
        last_possible_elm: int) -> list:
    current_position = step(position)
    context = []
    while can_iterate(current_position, end):
        if list_of_words[current_position] in [placeholders['loggable_block'], placeholders['loggable_block_end']]:
            if can_iterate(end, last_possible_elm):
                end = step(end)
        else:
            context.append(list_of_words[current_position])
        current_position = step(current_position)
    context += (['<pad>'] * (WORDS_IN_CONTEXT_LIMIT - len(context)))
    return context


def create_case(list_of_words: list, position: int) -> (list, list):
    before = create_side_of_case(list_of_words=list_of_words,
                                 position=position,
                                 end=max(-1, position - WORDS_IN_CONTEXT_LIMIT - 1),
                                 step=lambda i: i - 1,
                                 can_iterate=lambda iter, border: iter > border,
                                 last_possible_elm=-1)
    before.reverse()

    after = create_side_of_case(list_of_words=list_of_words,
                                position=position,
                                end=min(position + WORDS_IN_CONTEXT_LIMIT + 1, len(list_of_words)),
                                step=lambda i: i + 1,
                                can_iterate=lambda iter, border: iter < border,
                                last_possible_elm=len(list_of_words))

    return before, after


def extract_loggable_blocks_positions(list_of_words: List[str]) -> List[Tuple[int, int]]:
    blocks = []
    search_start_position = 0
    while True:
        try:
            block_start_pos = list_of_words.index(placeholders['loggable_block'], search_start_position)
        except ValueError:
            break
        try:
            block_end_pos = list_of_words.index(placeholders['loggable_block_end'], block_start_pos + 1)
        except ValueError:
            logger.warning("Invalid file. Loggable block end not found: {}")
            break
        blocks.append((block_start_pos + 1, block_end_pos - 1))
        search_start_position = block_end_pos + 1
    return blocks


def get_possible_log_locations(list_of_words: List[str]) -> List[int]:
    '''
    possible places where we insert:
    - after semicolon
    - after {
    - after {
    '''
    locations = []
    symbol_to_insert_after = ['{', '}', ';']
    blocks_positions = extract_loggable_blocks_positions(list_of_words)
    for start, end in blocks_positions:
        for i in range(start, end):
            if list_of_words[i] in symbol_to_insert_after:
                locations.append(i + 1)
    return locations

def create_negative_case(list_of_words):
    indices = get_possible_log_locations(list_of_words)
    if indices:
        position = random.choice(indices)
        list_of_words.insert(position, 'fake log st')
        return create_case(list_of_words, position)
    else:
        return None


def create_positive_case(list_of_words):
    indices = [i for i, x in enumerate(list_of_words) if x == placeholders['log_statement']]
    if indices:
        position = random.choice(indices)
    else:
        raise AssertionError("")
    return create_case(list_of_words, position)


def do(filename):
    rel_path = get_dir_and_file(filename)
    with open(filename, 'r') as f:
        res = []
        os.path.join(filename)
        for line in f:
            line = line if line[-1] != '\n' else line[:-1]
            list_of_words = line.split(" ")
            if placeholders['log_statement'] in list_of_words:
                res.append((create_positive_case(list_of_words), True))
            else:
                case = create_negative_case(list_of_words)
                if case:
                    res.append((case, False))
    return res, rel_path

def run(full_src_dir, dest_dir):
    total_files = sum(file_mapper(full_src_dir, lambda f: 1, "parsed.repr"))
    count = 0
    for lines, rel_path in file_mapper(full_src_dir, do, "parsed.repr"):
        count += 1
        logger.info(f"Processing {count} out of {total_files}")
        forward_path = os.path.join(dest_dir, re.sub("parsed\\.repr", ContextsDataset.FW_CONTEXTS_FILE_EXT, rel_path))
        backward_path = os.path.join(dest_dir, re.sub("parsed\\.repr", ContextsDataset.BW_CONTEXTS_FILE_EXT, rel_path))
        label_path = os.path.join(dest_dir, re.sub("parsed\\.repr", ContextsDataset.LABEL_FILE_EXT, rel_path))
        with open(forward_path, 'w') as f, open(backward_path, 'w') as b, open(label_path, 'w') as l:
            for line in lines:
                l.write(f'{1 if line[1] else 0}\n')
                f.write(f'{" ".join(line[0][0])}\n')
                b.write(f'{" ".join(line[0][1])}\n')


if __name__ == '__main__':
    from logrec.local_properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_DATASET_GENERATOR_ARGS

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--base', action='store', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('dataset', action='store', help=f'path to the repr dataset')
    parser.add_argument('repr', action='store', help=f'path to the repr dataset')

    args = parser.parse_known_args(*DEFAULT_DATASET_GENERATOR_ARGS)
    args = args[0]

    path_to_dataset = os.path.join(args.base, args.dataset)
    full_src_dir = os.path.join(path_to_dataset, REPR_DIR, args.repr)
    clas9n_dataset_name = PrepParamsParser.to_classification_prep_params(args.repr)
    dest_dir = os.path.join(path_to_dataset, CLASSIFICATION_DIR_NAME, CLASSIFICATION_TYPE, clas9n_dataset_name)
    logger.info(f"Writing to {dest_dir}")

    os.makedirs(os.path.join(dest_dir, TRAIN_DIR), exist_ok=True)
    os.makedirs(os.path.join(dest_dir, TEST_DIR), exist_ok=True)
    os.makedirs(os.path.join(dest_dir, VALID_DIR), exist_ok=True)

    run(full_src_dir, dest_dir)
