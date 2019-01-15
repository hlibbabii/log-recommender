import argparse
import logging
import os
import random
import re
from typing import List, Tuple, Callable, Optional

from logrec.classifier.utils import get_dir_and_file

from logrec.dataprep import REPR_DIR, TRAIN_DIR, TEST_DIR, VALID_DIR, CLASSIFICATION_DIR
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.util.io_utils import file_mapper

WORDS_IN_CONTEXT_LIMIT = 1000

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
        if list_of_words[current_position] in [placeholders['loggable_block'], placeholders['loggable_block_end']] \
                or (list_of_words[current_position] == placeholders["log_statement"] and random.choice([True, False])):
            if can_iterate(end, last_possible_elm):
                end = step(end)
        else:
            context.append(list_of_words[current_position])
        current_position = step(current_position)
    context += ([placeholders['pad_token']] * (WORDS_IN_CONTEXT_LIMIT - len(context)))
    return context


def create_case(list_of_words: list, position_range: (int, int)) -> (list, list):
    before = create_side_of_case(list_of_words=list_of_words,
                                 position=position_range[0],
                                 end=max(-1, position_range[0] - WORDS_IN_CONTEXT_LIMIT - 1),
                                 step=lambda i: i - 1,
                                 can_iterate=lambda iter, border: iter > border,
                                 last_possible_elm=-1)
    before.reverse()

    after = create_side_of_case(list_of_words=list_of_words,
                                position=position_range[1],
                                end=min(position_range[1] + WORDS_IN_CONTEXT_LIMIT + 1, len(list_of_words)),
                                step=lambda i: i + 1,
                                can_iterate=lambda iter, border: iter < border,
                                last_possible_elm=len(list_of_words))

    return before, after


def get_position_ranges_between_tokens(list_of_words: List[str], token1: str, token2: str, suppress_error=True) -> List[
    Tuple[int, int]]:
    ranges = []
    search_start_position = 0
    while True:
        try:
            range_start = list_of_words.index(token1, search_start_position)
        except ValueError:
            break
        try:
            range_end = list_of_words.index(token2, range_start + 1)
        except ValueError:
            error_text = f'token2 ({token2}) corresponding to token1 ({token1}) not found: {list_of_words[range_start:range_start+25]}'
            if suppress_error:
                logger.warning(f"Interrupting processing: {error_text}")
                break
            else:
                raise ValueError(error_text)
        ranges.append((range_start, range_end))
        search_start_position = range_end + 1
    return ranges


def extract_loggable_blocks_positions(list_of_words: List[str]) -> List[Tuple[int, int]]:
    ranges = get_position_ranges_between_tokens(list_of_words,
                                                placeholders['loggable_block'],
                                                placeholders['loggable_block_end'])
    blocks = [(start + 1, end - 1) for start, end in ranges]
    return blocks


def get_possible_log_locations(list_of_words: List[str]) -> List[int]:
    '''
    possible places where we insert:
    - after semicolon
    - after {
    - after {
    - after a Log statement
    '''
    locations = []
    symbol_to_insert_after = ['{', '}', ';', placeholders['log_statement_end']]
    blocks_positions = extract_loggable_blocks_positions(list_of_words)
    for start, end in blocks_positions:
        for i in range(start, end):
            if list_of_words[i] in symbol_to_insert_after:
                locations.append(i + 1)
    return locations


def create_negative_case(list_of_words: List[str]) -> Optional[Tuple[List[str], List[str]]]:
    indices = get_possible_log_locations(list_of_words)
    if indices:
        position_range = random.choice(indices)
        list_of_words.insert(position_range, 'fake log st')
        return create_case(list_of_words, (position_range, position_range))
    else:
        logger.warning(f"Loggable blocks not found, but should be: {list_of_words}")
        return None


def extract_level_label(list_of_words: List[str], position_range: Tuple[int, int]) -> str:
    return list_of_words[position_range[0] + 1]


def create_positive_case(list_of_words: List[str]) -> (list, list):
    position_ranges = get_position_ranges_between_tokens(list_of_words, placeholders['log_statement'],
                                                         placeholders['log_statement_end'], suppress_error=False)
    if position_ranges:
        position_range = random.choice(position_ranges)
    else:
        raise AssertionError("")

    contexts = create_case(list_of_words, position_range)
    level = extract_level_label(list_of_words, position_range)
    return contexts, level


def create_log_position_cases(filename: str) -> Tuple[List[Optional[Tuple[List[str], List[str], bool]]], str]:
    rel_path = get_dir_and_file(filename)
    with open(filename, 'r') as f:
        res = []
        os.path.join(filename)
        for line in f:
            list_of_words = line.rstrip('\n').split(" ")
            if placeholders['log_statement'] in list_of_words:
                if random.choice([True, False]):
                    contexts, _ = create_positive_case(list_of_words)
                    res.append((*contexts, 1))
                else:
                    case = create_negative_case(list_of_words)
                    if case:
                        res.append((*case, 0))
                    else:
                        res.append(None)
            else:
                res.append(None)
    return res, rel_path


def create_level_cases(filename: str) -> Tuple[List[Optional[Tuple[List[str], List[str], bool]]], str]:
    rel_path = get_dir_and_file(filename)
    with open(filename, 'r') as f:
        res = []
        os.path.join(filename)
        for line in f:
            list_of_words = line.rstrip('\n').split(" ")
            if placeholders['log_statement'] in list_of_words:
                contexts, level = create_positive_case(list_of_words)
                res.append((*contexts, level))
            else:
                res.append(None)
    return res, rel_path


def get_cases_creator(classifier):
    if classifier == 'location':
        return create_log_position_cases
    elif classifier == 'level':
        return create_level_cases
    else:
        raise ValueError(f'Unknown classifier: {classifier}')


def run(dataset: str, repr: str, classifier: str):
    from logrec.classifier.context_datasets import ContextsDataset

    path_to_dataset = os.path.join(DEFAULT_PARSED_DATASETS_DIR, dataset)
    full_src_dir = os.path.join(path_to_dataset, REPR_DIR, repr)
    dest_dir = os.path.join(path_to_dataset, CLASSIFICATION_DIR, classifier, args.repr)
    logger.info(f"Writing to {dest_dir}")

    os.makedirs(os.path.join(dest_dir, TRAIN_DIR), exist_ok=True)
    os.makedirs(os.path.join(dest_dir, TEST_DIR), exist_ok=True)
    os.makedirs(os.path.join(dest_dir, VALID_DIR), exist_ok=True)

    total_files = sum(file_mapper(full_src_dir, lambda f: 1, "parsed.repr"))
    count = 0

    cases_creator = get_cases_creator(classifier)
    for lines, rel_path in file_mapper(full_src_dir, cases_creator, "parsed.repr"):
        count += 1
        logger.info(f"Processing {count} out of {total_files}")
        forward_path = os.path.join(dest_dir, re.sub("parsed\\.repr", ContextsDataset.FW_CONTEXTS_FILE_EXT, rel_path))
        backward_path = os.path.join(dest_dir, re.sub("parsed\\.repr", ContextsDataset.BW_CONTEXTS_FILE_EXT, rel_path))
        label_path = os.path.join(dest_dir, re.sub("parsed\\.repr", ContextsDataset.LABEL_FILE_EXT, rel_path))
        with open(forward_path, 'w') as f, open(backward_path, 'w') as b, open(label_path, 'w') as l:
            for line in lines:
                if line:
                    l.write(f'{line[2]}\n')
                    f.write(f'{" ".join(line[0])}\n')
                    b.write(f'{" ".join(line[1])}\n')
                else:
                    l.write('\n')
                    f.write('\n')
                    b.write('\n')


if __name__ == '__main__':
    from logrec.properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_DATASET_GENERATOR_ARGS

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('dataset', action='store', help=f'path to the repr dataset')
    parser.add_argument('repr', action='store', help=f'path to the repr dataset')
    parser.add_argument('classifier', action='store', help=f'classifier type: location|level')

    args = parser.parse_known_args(*DEFAULT_DATASET_GENERATOR_ARGS)
    args = args[0]

    run(args.dataset, args.repr, args.classifier)
