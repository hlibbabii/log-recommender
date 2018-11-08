import logging
from collections import defaultdict

from logrec.dataprep.split.samecase.typo_fixer import is_typo

logger = logging.getLogger(__name__)

def assert_split(split_line):
    if len(split_line) != 3:
        raise AssertionError(f"Type is split but no splitting to subwords: {split_line}")
    original = split_line[0]
    subwords = split_line[2]
    split_subwords = subwords.split()
    if len(split_subwords) <= 1:
        raise AssertionError(f"Type is split but word actually not split: {original}")
    if original != ''.join(split_subwords):
        raise AssertionError(f"Original word is {original}, but split seq is {split_subwords}")


def assert_typo(split_line):
    if len(split_line) != 3:
        raise AssertionError(f"Type is split but no typo fix: {split_line}")
    original = split_line[0]
    typo_fix = split_line[2]
    if not is_typo(original, typo_fix):
        raise AssertionError(f"{typo_fix} is not typo fix of {original}")


def assert_non_split(split_line):
    if len(split_line) != 2:
        raise AssertionError(f"There should 2 entries in this line: {split_line}")

def create_types_to_conversions_assertions():
    types_to_convertion_assertions = {
        'spl': assert_split,
        'nonspl': assert_non_split,
        'rnd': assert_non_split,
        'typo': assert_typo
    }

    lang_code_list = ['de', 'sp', 'pt', 'fr', 'sv', 'da', 'nl', 'fi', 'hr', 'et']

    for lang_code in lang_code_list:
        types_to_convertion_assertions[lang_code] = assert_non_split
    return types_to_convertion_assertions

TYPES_TO_CONVERSIONS_ASSERTIONS = create_types_to_conversions_assertions()

def check_line(split_line):
    if len(split_line) <= 1:
        raise AssertionError(f"There should be at least 2 entries in this line: {split_line}")
    type = split_line[1]
    if type in TYPES_TO_CONVERSIONS_ASSERTIONS:
        TYPES_TO_CONVERSIONS_ASSERTIONS[type](split_line)
    else:
        raise AssertionError(f'Unknown type: {type}')


def read(path_to_file):
    stats = defaultdict(list)
    words_to_split = {}
    sample_word_length_stats = defaultdict(int)
    with open(path_to_file, 'r') as f:
        for line in f:
            split_line = line[:-1].split('|')
            check_line(split_line)
            type = split_line[1]
            original_word = split_line[0]
            stats[type].append((original_word, split_line[2]) if type == 'spl' else original_word)
            if type == 'spl' or type == 'nonspl':
                words_to_split[original_word] = type
            sample_word_length_stats[len(original_word)] += 1
    sample_word_length_stats.default_factory = None
    return stats, words_to_split


