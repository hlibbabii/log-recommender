import csv
import logging
import os
from pprint import pprint

from fastai.imports import tqdm
from logrec.dataprep import base_project_dir
from logrec.dataprep.lang.param_mutator import ParamMutator
from logrec.dataprep.split.samecase import manually_tagged_splittings_file_reader
from logrec.dataprep.split.samecase.splitter import load_english_dict, get_splittings

logger = logging.getLogger(__name__)

base_dataset_dir = f'{base_project_dir}/nn-data/devanbu_no_replaced_identifier_split_no_tabs_new_splits3_under_5000_15_percent/'
path_manually_tagged_splittings = os.path.join(base_project_dir, 'manually_tagged_splittings.txt')
path_to_mutations = os.path.join(base_dataset_dir, 'mutations.csv')
path_to_general_dictionary = '/usr/share/dict/words'


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

def print_different_token_types_stats(stats):
    pprint(stats)
    for s, lst in stats.items():
        print(f'{s} -- {len(lst)}')


def convert_to_params(keys, mutations):
    res = []
    for mutation in mutations:
        res.append({k: v for k, v in zip(keys, mutation)})
    return res


if __name__ == '__main__':
    stats, words_to_split = manually_tagged_splittings_file_reader.read(path_manually_tagged_splittings)

    print_different_token_types_stats(stats)

    # TODO fix and clean this up!
    # dataset_name = nn_params["dataset_name"]
    # path_to_dataset = os.path.join(nn_params["path_to_data"], dataset_name)
    # path_to_splits = os.path.join(path_to_dataset, 'splits')
    path_to_dataset = None
    path_to_splits = None

    general_dict = load_english_dict(os.path.join(base_project_dir, 'dicts', 'eng'))

    possibel_var_values, (keys, mutations) = ParamMutator(
        [{'name': 'alpha', 'start': 0.1, 'end': 1000000.0, 'plus_or_mult': 'mult', 'koef': 2.0},
         {'name': 'beta', 'start': 1.0, 'end': 1000.0, 'plus_or_mult': 'mult', 'koef': 1.2},
         {'name': 'gamma', 'start': 0.1, 'end': 1000000.0, 'plus_or_mult': 'mult', 'koef': 2.0},
         {'name': 'lambda_', 'start': 1.0, 'end': 6.0, 'plus_or_mult': 'plus', 'koef': 1.15},
         {'name': 'theta', 'start': 1.0, 'end': 6.0, 'plus_or_mult': 'plus', 'koef': 1.15},
         {'name': 'd', 'start': 1.0, 'end': 100.0, 'plus_or_mult': 'mult', 'koef': 1.5}]) \
        .mutate(5000, 1000)

    freqs = io.read_dict_from_2_columns(os.path.join(path_to_dataset, 'vocab.txt'))

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
