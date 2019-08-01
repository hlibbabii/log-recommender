import argparse
import logging
import os
import random

import dataprep
from typing import List, Tuple, Callable, Union, Dict

from langmodels.inference.model import TrainedModel
from langmodels.profiling import TimeMeasurer

logger = logging.getLogger(__name__)

time_measurer = TimeMeasurer()

MAX_BATCH_SIZE = 20


def get_max_batch_size():
    return MAX_BATCH_SIZE


def file_fitter(sizes: List[int], n: int) -> Tuple[List[List[int]], List[List[int]]]:
    if n <= 0:
        raise ValueError("N must be > 0")

    random.shuffle(sizes)
    layout = [[] for _ in range(n)]
    boundaries = [[0] for _ in range(n)]
    for idx, size in enumerate(sizes):
        layout[idx % n].append(idx)
        boundaries[idx % n].append(boundaries[idx % n][-1] + size)
    return layout, boundaries


def repackage(lines_list: List[List[str]], layout:List[List[int]]):
    new_list = []
    for column in layout:
        list_column = []
        for idx in column:
            list_column.extend(lines_list[idx])
        new_list.append(list_column)
    return new_list


def make_batches_equal(repackage_lines: List[List[str]]):
    max_batch_size = max(map(lambda l: len(l), repackage_lines))
    for lines in repackage_lines:
        n_lines_to_add = max_batch_size - len(lines)
        for _ in range(n_lines_to_add):
            lines.append('\n')
    return repackage_lines


def get_list_of_line_lists_from_dir(dir: str) -> Tuple[List[List[str]], List[str]]:
    files_full_paths = [os.path.join(root, file) for root, dirs, files in os.walk(dir) for file in files]
    lines_list = []
    file_list = []
    for file in files_full_paths:
        with open(file, 'r') as f:
            lines = [line for line in f]
        lines_list.append(lines)
        file_list.append(file)
    return lines_list, file_list


def get_lines(path: str) -> Tuple[List[List[str]], List[List[str]], List[List[int]]]:
    if os.path.isfile(path):
        with open(path, 'r') as f:
            lines_list, file_list = [[line for line in f]], [path]
    else:
        lines_list, file_list = get_list_of_line_lists_from_dir(path)
    batch_size = min(get_max_batch_size(), len(lines_list))
    layout, boundaries = file_fitter(list(map(lambda l: len(lines_list), lines_list)), batch_size)
    repackaged_files = repackage(list(map(lambda f: [f], file_list)), layout)
    repackaged_lines = repackage(lines_list, layout)
    return [list(e) for e in zip(*make_batches_equal(repackaged_lines))], repackaged_files, boundaries


def unpackage_entropies(line_entropies_columns: List[List[str]],
                        files: List[List[str]],
                        boundaries: List[List[int]]) -> Dict[str, List[float]]:
    res = {}
    for column, files_in_column, boundaries_in_column in zip(line_entropies_columns, files, boundaries):
        for idx, file in enumerate(files_in_column):
            res[file] = column[boundaries_in_column[idx]: boundaries_in_column[idx+1]]
    return res


def get_entopy_for_each_line(trained_model: TrainedModel,
                             path: str,
                             entropy_aggregator: Callable[[List[float], List[int]], Union[float, List[float]]],
                             verbose: bool = False) -> Dict[str, float]:
    prep_lines_and_entropies: List[Tuple[List[str], List[float], float]] = []
    lines_list, files, boundaries = get_lines(path)
    trained_model.set_batch_size(len(files))
    for lines in lines_list:
        time_measurer.tick("Preprocessing")
        metadata_list = []
        prep_lines = []
        for line in lines:
            prep_line, metadata = dataprep.bpe(line, trained_model.get_bpe_codes_id(), extension="java", **trained_model.get_prep_params(), return_metadata=True)
            prep_lines.append(prep_line)
            metadata_list.append(metadata)
        time_measurer.tock("Preprocessing")
        time_measurer.tick("Inference")
        entropies_batch = trained_model.get_entropies_for_next(prep_lines)
        time_measurer.tock("Inference")
        for entropies, m in zip(entropies_batch, metadata_list):
            line_entropy = entropy_aggregator(entropies, m.word_boundaries)
            prep_lines_and_entropies.append((prep_line, entropies, line_entropy))
        if verbose:
            for prep_line, entropies, line_entropy in prep_lines_and_entropies:
                print(f'{[(prep_token, token_entropy) for prep_token, token_entropy in zip(prep_line, entropies)]}')
                print(line_entropy)
                print("=============")
    line_entropies_columns = list(zip(*prep_lines_and_entropies))[2]
    return unpackage_entropies(line_entropies_columns, files, boundaries)


def subword_average(subword_entropies: List[float], word_boundaries: List[int]) -> float:
    return sum(subword_entropies) / len(subword_entropies) if subword_entropies else .0


def word_entropy_list(subword_entropies: List[float], word_boundaries: List[int]) -> List[float]:
    if not word_boundaries or word_boundaries[-1] != len(subword_entropies):
        raise ValueError(f"Word boundaries list should contain the index of the last word "
                         f"(or at least 0 if subword_entropies list is empty).\n"
                         f"However, the subword entropies list has {len(subword_entropies)} elements, and "
                         f"value {len(subword_entropies)} is not found in word boundaries list: {word_boundaries}")

    word_entropies = []
    for i in range(len(word_boundaries) - 1):
        word_start_index = word_boundaries[i]
        word_end_index = word_boundaries[i+1]
        word_entropies.append(sum(subword_entropies[word_start_index: word_end_index]))
    return word_entropies


def word_average(subword_entropies: List[float], word_boundaries: List[int]) -> float:
    word_entropies = word_entropy_list(subword_entropies, word_boundaries)
    if not word_entropies:
        return .0

    return sum(word_entropies) / len(word_entropies)


def parse_entropy_aggregator_value(entropy_aggregator_name: str) -> Callable[[List[float], List[int]], Union[float, List[float]]]:
    if entropy_aggregator_name == 'subtoken-average':
        return subword_average
    elif entropy_aggregator_name == 'full-token-average':
        return word_average
    elif entropy_aggregator_name == 'full-token-entropies':
        return word_entropy_list
    else:
        raise ValueError(f"Unknown value for entropy aggregator: {entropy_aggregator_name}")


def write_entropies_to_disk(entropies: Dict[str, List[float]], output_path: str):
    if list(entropies.keys()) == ['']:
        with open(output_path, 'w') as f:
            for entropy in entropies['']:
                f.write(f'{entropy}\n')
    else:
        for file, entropies in entropies:
            full_path = os.path.join(output_path, file)
            with open(full_path, 'w') as f:
                if not os.path.exists(full_path):
                    for entropy in entropies:
                        f.write(f'{entropy}\n')

    print(f'Entropies are written to {args.output_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', action='store', help=f'Path to file or dir for which entropies are to be calculated.')
    parser.add_argument('-o', '--output-path', action='store', help='Path to file or dir to which entropies are to be written.')
    parser.add_argument('-e', '--entropy-aggregator', action='store', default='full-token-average',
                        help='Fuction to calculate entropy for the whole line from subtoken entropies. Possible values:\n'
                             '\'subtoken-average\' (default): average over all subtokens\' entropies \n'
                             '\'full-token-average\': average over all full-tokens\' entopies '
                             '(entropy of a full token is a sum of entopies of its subtokens to which a token was split during pre-processing) \n'
                             '\'full-token-entropies\': a list of full-token entropies (gives freedom to library\'s clients to compute line-entropy in their own way) \n')
    parser.add_argument('-c', '--cpu', action='store_true', help='Forse cpu usage for inference even if cuda-supported GPU is available.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Write preprocessed lines and their entropies to stdout.')
    args = parser.parse_args()
    verbose = args.verbose or not args.output_path

    time_measurer.tick('Model loading')
    model = TrainedModel.get_default_model(force_use_cpu=args.cpu)
    time_measurer.tock('Model loading')
    entropy_aggregator = parse_entropy_aggregator_value(args.entropy_aggregator)
    entropies = get_entopy_for_each_line(model, args.path, entropy_aggregator, verbose)
    if args.output_path:
        write_entropies_to_disk(entropies, args.output_path)

    if verbose:
        totals = time_measurer.totals()
        for what, total_time in totals.items():
            logger.debug(f'{what} took {total_time:.4f} s')