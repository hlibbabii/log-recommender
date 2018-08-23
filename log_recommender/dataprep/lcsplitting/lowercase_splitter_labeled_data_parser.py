import csv
import logging
from collections import defaultdict
from pprint import pprint

from dataprep import base_project_dir
from dataprep.lcsplitting.lowercase_words_splitter import get_splittings, load_english_dict
from dataprep.lcsplitting.param_mutator import ParamMutator
from dataprep.lcsplitting.typo_fixer import is_typo
from fastai.imports import tqdm
from nn.params import nn_params

logging.basicConfig(level=logging.INFO)

base_dataset_dir = f'{base_project_dir}/nn-data/devanbu_no_replaced_identifier_split_no_tabs_new_splits3_under_5000_15_percent/'
path_to_labeled_data = f'{base_dataset_dir}/sample.txt'
path_to_mutations = f'{base_dataset_dir}/mutations.csv'
path_to_general_dictionary = '/usr/share/dict/words'


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


types_to_convertion_assertions = {
    'spl': assert_split,
    'nonspl': assert_non_split,
    'rnd': assert_non_split,
    'typo': assert_typo
}

lang_code_list = ['de', 'sp', 'pt', 'fr', 'sv', 'da', 'nl', 'fi', 'hr', 'et']

for lang_code in lang_code_list:
    types_to_convertion_assertions[lang_code] = assert_non_split


def check_line(split_line):
    if len(split_line) <= 1:
        raise AssertionError(f"There should be at least 2 entries in this line: {split_line}")
    type = split_line[1]
    if type in types_to_convertion_assertions:
        types_to_convertion_assertions[type](split_line)
    else:
        raise AssertionError(f'Unknown type: {type}')


class ErrorStats(object):
    not_the_same_weight = 0.6
    fp_weight = 0.2
    fn_weight = 0.2

    def __init__(self, total_error, fp_error, fn_error,
                 fp_not_same_error, fps, fns, not_the_same):
        self.total_error = total_error
        self.fp_error = fp_error
        self.fn_error = fn_error
        self.fp_not_same_error = fp_not_same_error
        self.fps = fps
        self.fns = fns
        self.not_the_same = not_the_same

    def weighted_error(self):
        return self.fp_not_same_error * self.not_the_same_weight + self.fp_error * self.fp_weight \
               + self.fn_error * self.fn_weight

    def __str__(self):
        return ', '.join('%s=%s' % item for item in vars(self).items())

    def __repr__(self):
        return self.__str__()

    def get_short_stats(self):
        return {'fps': self.fp_error, 'fns': self.fn_error, 'not_the_same': self.fp_not_same_error,
                'weighted': self.weighted_error(), 'total': self.total_error}


def compute_error_stats(split_actual, nonsplit_actual, split_expected, nonsplit_expected):
    tp_same, tp_not_same, tn, fp, fn = 0, 0, 0, 0, 0
    fps = []
    fns = []
    not_the_same = []
    for k, v in split_actual.items():
        if k in split_expected:
            if split_expected[k] == ' '.join(split_actual[k]):
                tp_same += 1
            else:
                tp_not_same += 1
                not_the_same.append((split_expected[k], ' '.join(split_actual[k])))
        else:
            fp += 1
            fps.append(k)
    for na in nonsplit_actual:
        if na in nonsplit_expected:
            tn += 1
        else:
            fn += 1
            fns.append(na)
    total = float(len(split_expected) + len(nonsplit_expected))
    total_error = (fp + fn + tp_not_same) / total
    fp_error = fp / total
    fn_error = fn / total
    fp_not_same_error = tp_not_same / total

    return ErrorStats(total_error=total_error,
                      fp_error=fp_error,
                      fn_error=fn_error,
                      fp_not_same_error=fp_not_same_error,
                      fps=fps,
                      fns=fns,
                      not_the_same=not_the_same)


data = []
stats = defaultdict(list)
words_to_split = {}
sample_word_length_stats = defaultdict(int)
with open(path_to_labeled_data, 'r') as f:
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


def print_different_token_types_stats(stats):
    pprint(stats)
    for s, lst in stats.items():
        print(f'{s} -- {len(lst)}')


print_different_token_types_stats(stats)

dataset_name = nn_params["dataset_name"]
path_to_dataset = f'{nn_params["path_to_data"]}/{dataset_name}'
path_to_splits = f'{path_to_dataset}/splits'

general_dict = load_english_dict(f'{base_project_dir}/dicts/eng')

possibel_var_values, (keys, mutations) = ParamMutator(
    [{'name': 'alpha', 'start': 0.1, 'end': 1000000.0, 'plus_or_mult': 'mult', 'koef': 2.0},
     {'name': 'beta', 'start': 1.0, 'end': 1000.0, 'plus_or_mult': 'mult', 'koef': 1.2},
     {'name': 'gamma', 'start': 0.1, 'end': 1000000.0, 'plus_or_mult': 'mult', 'koef': 2.0},
     {'name': 'lambda_', 'start': 1.0, 'end': 6.0, 'plus_or_mult': 'plus', 'koef': 1.15},
     {'name': 'theta', 'start': 1.0, 'end': 6.0, 'plus_or_mult': 'plus', 'koef': 1.15},
     {'name': 'd', 'start': 1.0, 'end': 100.0, 'plus_or_mult': 'mult', 'koef': 1.5}]) \
    .mutate(5000, 1000)


def convert_to_params(keys, mutations):
    res = []
    for mutation in mutations:
        res.append({k: v for k, v in zip(keys, mutation)})
    return res


freqs = {}
with open(f'{path_to_dataset}/vocab.txt', 'r') as f:
    for l in f:
        line = l.split(" ")
        freqs[line[0]] = int(line[1])

print(possibel_var_values)
print("======================")
pprint(mutations)
print("======================")
with open(path_to_mutations, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    params = convert_to_params(keys, mutations)
    # params = [{
    #     'alpha': 9.0,
    #     'beta': 5.0,
    #     'gamma': 3.0,
    #     'lambda_': 2.0,
    #     'theta': 2.0,
    #     'd': 10.0
    # }]
    n_iter = len(mutations)
    # n_iter=1
    for ind, params in tqdm(enumerate(params), total=n_iter):
        transformed, nontransformed, possible_typos = get_splittings(
            words_to_split.keys(),
            freqs, general_dict, params)

        error_stats = compute_error_stats({k: v["subwords_set"] for k, v in transformed.items()}, nontransformed,
                                          {k: v for k, v in stats['spl']}, stats['nonspl'])

        print(f'Param set # {ind}')
        pprint(params)
        pprint(error_stats)
        print('====================================')

        writer.writerow(list(params.values()) + list(error_stats.get_short_stats().values()))
