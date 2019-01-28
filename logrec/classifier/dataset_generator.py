import argparse
import logging
import os
import random
import re
from functools import partial
from typing import List, Tuple, Callable, Optional, Union


from logrec.dataprep import REPR_DIR, TRAIN_DIR, TEST_DIR, VALID_DIR, CLASSIFICATION_DIR
from logrec.dataprep.model.logging import is_positive_level
from logrec.dataprep.model.placeholders import placeholders
from logrec.util.files import get_dir_and_file, file_mapper

WORDS_IN_CONTEXT_LIMIT = 1000

logger = logging.getLogger(__name__)


def create_case(list_of_words: list, position_range: (int, int)) -> (list, list):
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
        context += ([placeholders['pad_token']] * (WORDS_IN_CONTEXT_LIMIT - len(context)))
        return context

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


def remove_ranges_from_list(lst: list, ranges: List[Tuple[int, int]]) -> list:
    res = []
    start = 0
    for index_from, index_to in ranges:
        end = index_from
        res.extend(lst[start:end])
        start = index_to
    res.extend(lst[start:])
    return res


def get_position_ranges_between_tokens(list_of_words: List[str],
                                       token1: str,
                                       token2: str, suppress_error=True) -> List[Tuple[int, int]]:
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


class CaseCreator(object):
    def __init__(self,
                 range_selector: Callable[
                     [List[
                          Tuple[int, int]]],
                     Union[
                         List[
                             Tuple[int, int]],
                         Tuple[int, int]
                     ]],
                 label_creator: Callable[[Optional[str]], str],
                 possible_positions_finder: Callable[
                     [List[str]],
                     List[
                         Tuple[int, int]
                     ]],
                 log_content_extractor: Callable[
                     [List[str], Tuple[int, int]],
                     Optional[str]
                 ]):

        self.range_selector = range_selector
        self.label_creator = label_creator
        self.possible_positions_finder = possible_positions_finder
        self.log_content_extractor = log_content_extractor

    def create_from(self, list_of_words: List[str]) -> (List[str], List[str], str):
        possible_ranges = self.possible_positions_finder(list_of_words)
        if possible_ranges:
            position_range = self.range_selector(possible_ranges)
        else:
            return None

        contexts = create_case(list_of_words, position_range)
        log_statement = self.log_content_extractor(list_of_words, position_range)
        return contexts[0], contexts[1], self.label_creator(log_statement)


######################   Possible position finders    ####################################33

def get_existing_log_locations(list_of_words: List[str]) -> List[Tuple[int, int]]:
    """

    :param list_of_words:
    :return: list of ranges [(i1, j1)...] where i1 is the index of teh first `L, j1 - index of the xorresponding L`
    """
    return get_position_ranges_between_tokens(list_of_words, placeholders['log_statement'],
                                              placeholders['log_statement_end'], suppress_error=False)


def get_possible_log_locations(list_of_words: List[str]) -> List[Tuple[int, int]]:
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
                locations.append((i + 1, i))
    return locations


###################### Log content extractors   #####################

def extract_level_label(list_of_words: List[str], position_range: Tuple[int, int]) -> str:
    return list_of_words[position_range[0] + 1]


#####################

def remove_some_log_statements(list_of_words):
    ranges = get_existing_log_locations(list_of_words)
    n_logs_to_remove = random.randint(0, len(ranges))
    ranges_of_logs_to_remove = random.sample(ranges, n_logs_to_remove)
    return remove_ranges_from_list(list_of_words, list(map(lambda a: (a[0], a[1] + 1), ranges_of_logs_to_remove)))


def create_cases(case_creators, case_creators_picker, filename: str) -> Tuple[
    List[Optional[Tuple[List[str], List[str], bool]]], str]:
    rel_path = get_dir_and_file(filename)
    with open(filename, 'r') as f:
        res = []
        for line in f:
            list_of_words = line.rstrip('\n').split(" ")
            list_of_words = remove_some_log_statements(list_of_words)
            if placeholders['log_statement'] in list_of_words:
                case_creator = case_creators_picker(case_creators)
                res.append(case_creator.create_from(list_of_words))
            else:
                res.append(None)
    return res, rel_path


def get_cases_creator(classifier):
    position_positive = CaseCreator(range_selector=random.choice,
                                    label_creator=lambda l: '1',
                                    possible_positions_finder=get_existing_log_locations,
                                    log_content_extractor=lambda *_: None
                                    )

    position_negative = CaseCreator(range_selector=random.choice,
                                    label_creator=lambda l: '0',
                                    possible_positions_finder=get_possible_log_locations,
                                    log_content_extractor=lambda *_: None)

    level = CaseCreator(range_selector=random.choice,
                        label_creator=lambda l: l,
                        possible_positions_finder=get_existing_log_locations,
                        log_content_extractor=extract_level_label)

    level_binary = CaseCreator(range_selector=random.choice,
                               label_creator=lambda l: '1' if is_positive_level(l) else '0',
                               possible_positions_finder=get_existing_log_locations,
                               log_content_extractor=extract_level_label)

    if classifier == 'location':
        return partial(create_cases, [position_positive, position_negative], random.choice)
    elif classifier == 'level':
        return partial(create_cases, [level], lambda lst: lst[0])
    elif classifier == 'level_binary':
        return partial(create_cases, [level_binary], lambda lst: lst[0])
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

    parser = argparse.ArgumentParser()
    parser.add_argument('dataset', action='store', help=f'path to the repr dataset')
    parser.add_argument('repr', action='store', help=f'path to the repr dataset')
    parser.add_argument('classifier', action='store', help=f'classifier type: location|level')

    args = parser.parse_known_args(*DEFAULT_DATASET_GENERATOR_ARGS)
    args = args[0]

    run(args.dataset, args.repr, args.classifier)
