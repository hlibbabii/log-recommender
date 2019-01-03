import argparse
import gzip
import json
import logging
import os
import pickle
import time
from abc import ABCMeta, abstractmethod
from multiprocessing.pool import Pool

from logrec.dataprep import base_project_dir, METADATA_DIR, BPE_DIR, PARSED_DIR
from logrec.dataprep.preprocessors.general import to_token_list
from logrec.dataprep.preprocessors.preprocessing_types import PreprocessingParam, get_types_to_be_repr, PrepParamsParser
from logrec.dataprep.preprocessors.repr import to_repr_list, ReprConfig
from logrec.dataprep.split.ngram import NgramSplittingType, NgramSplitConfig, SplitRepr
from logrec.util import io_utils

logger = logging.getLogger(__name__)

PARSED_FILE_EXTENSION = "parsed"
REPR_EXTENSION = "repr"
NOT_FINISHED_EXTENSION = "part"


def calc_new_preprocessing_types_dict(preprocessing_types_dict, preprocessing_types):
    if not isinstance(preprocessing_types_dict, dict):
        raise AssertionError("Should be preprocessing param dict!")
    new_preprocessing_types_dict = {}
    for (k, v) in preprocessing_types_dict.items():
        if v is None:
            new_preprocessing_types_dict[k] = preprocessing_types[k] if k in preprocessing_types else None
        elif k in preprocessing_types and preprocessing_types[k] != v:
            raise ValueError(f'Preprocessing {k} has already been applied with value {v}. '
                             f'Cannot be applied again with value {preprocessing_types[k]}')
        else:
            new_preprocessing_types_dict[k] = v

    got_pure_repr = None not in new_preprocessing_types_dict.values()
    return new_preprocessing_types_dict, got_pure_repr


class ReprWriter(metaclass=ABCMeta):
    def __init__(self, dest_file, mode, extension):
        self.dest_file = dest_file
        self.mode = mode
        self.extension = extension

    def __enter__(self):
        self.handle = open(f'{self.get_full_dest_name()}.{NOT_FINISHED_EXTENSION}', self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.handle.close()

    def get_full_dest_name(self):
        return f'{self.dest_file}.{self.extension}'

    @abstractmethod
    def write(self, token_list):
        '''Has to be implemented by subclasses'''


class FinalReprWriter(ReprWriter):
    def __init__(self, dest_file):
        super().__init__(dest_file, 'w', f'{REPR_EXTENSION}')

    def write(self, token_list):
        self.handle.write(to_token_list(token_list))


def check_preprocessing_params_are_valid(preprocessing_params):
    if preprocessing_params[PreprocessingParam.EN_ONLY] == 1 and preprocessing_params[PreprocessingParam.SPL] == 0:
        raise ValueError("both NO_SPL=0 and EN_ONLY=1 is not supported")


def to_repr(preprocessing_params, token_list, ngramSplittingConfig):
    """
    Preprocesses token list according to given preprocessing params
    :param preprocessing_params: e.g. {
        PreprocessingType.EN_ONLY: 1,
        PreprocessingType.NO_COM_STR: 0,
        PreprocessingType.SPL: 4,
        PreprocessingType.NO_SEP: 0
        PreprocessingType.NO_NEWLINES_TABS: 0,
        PreprocessingType.NO_LOGS: 0
    }
    :param token_list: list of tokens to be preprocessed
    :return:
    """
    check_preprocessing_params_are_valid(preprocessing_params)
    types_to_be_repr = get_types_to_be_repr(preprocessing_params)
    splitRepr = SplitRepr.BONDERIES if preprocessing_params[PreprocessingParam.NO_SEP] else SplitRepr.BETWEEN_WORDS
    repr_list = to_repr_list(token_list, ReprConfig(types_to_be_repr, ngramSplittingConfig, splitRepr))
    return repr_list


def preprocess_and_write(params):
    src_file, dest_file, preprocessing_params, old_preprocessing_params = params
    if not os.path.exists(src_file):
        logger.error(f"File {src_file} does not exist")
        exit(2)

    logger.info(f"Preprocessing parsed file {src_file}")
    with gzip.GzipFile(src_file, 'rb') as i:
        preprocessing_param_dict = pickle.load(i)
        if old_preprocessing_params != preprocessing_param_dict:
            logger.error(f"File {src_file} was expected to have preprocessing params "
                          f"{old_preprocessing_params}, but has {preprocessing_param_dict}")
            exit(221)
        new_preprocessing_param_dict, got_pure_repr = calc_new_preprocessing_types_dict(preprocessing_param_dict, preprocessing_params)
        writer = FinalReprWriter(dest_file)

        if os.path.exists(writer.get_full_dest_name()):
            logger.warning(f"File {writer.get_full_dest_name()} already exists! Doing nothing.")
            return
        with writer as w:
            if not got_pure_repr:
                w.write(new_preprocessing_param_dict)
            while True:
                try:
                    token_list = pickle.load(i)
                    repr = to_repr(preprocessing_params, token_list, ngramSplittingConfig)
                    w.write(repr)
                except EOFError:
                    break
    # remove .part to show that all raw files in this chunk have been preprocessed
    os.rename(f'{writer.get_full_dest_name()}.{NOT_FINISHED_EXTENSION}', f'{writer.get_full_dest_name()}')


def run(base_dir, dataset, preprocessing_params, bpe_base_repr, bpe_n_merges, splitting_file):
    full_src_dir = os.path.join(base_dir, args.dataset, PARSED_DIR)
    dest_dir = os.path.join(base_dir, args.dataset)

    if not os.path.exists(full_src_dir):
        logger.error(f"Dir does not exist: {full_src_dir}")
        exit(3)
    logger.info(f"Reading parsed files from: {os.path.abspath(full_src_dir)}")
    with open(os.path.join(full_src_dir, 'preprocessing_types.json'), 'r') as f:
        old_preprocessing_params_json = json.load(f)
    old_preprocessing_params = {PreprocessingParam(k): v for (k, v) in old_preprocessing_params_json.items()}
    logger.info(f"Old preprocessing params : {old_preprocessing_params}")

    preprocessing_params = PrepParamsParser.from_arg_str(preprocessing_params)
    global ngramSplittingConfig
    ngramSplittingConfig = NgramSplitConfig()
    if preprocessing_params[PreprocessingParam.SPL] == 4:
        if not bpe_base_repr or not bpe_n_merges:
            raise ValueError("--bpe-base-repr and --bpe-n-merges must be specified")

        path_to_merges_dir = os.path.join(DEFAULT_PARSED_DATASETS_DIR, dataset, METADATA_DIR, bpe_base_repr, BPE_DIR,
                                          bpe_n_merges)
        bpe_merges_file = os.path.join(path_to_merges_dir, 'merges.txt')
        bpe_merges_cache = os.path.join(path_to_merges_dir, 'merges_cache.txt')

        merges_cache = io_utils.read_dict_from_2_columns(bpe_merges_cache, val_type=list)
        merges = []
        with open(bpe_merges_file, 'r') as f:
            for line in f:
                line = line[:-1] if line[-1] == '\n' else line
                merges.append(line.split(' '))
        ngramSplittingConfig.merges_cache = merges_cache
        ngramSplittingConfig.merges = merges
        ngramSplittingConfig.set_splitting_type(NgramSplittingType.BPE)
    elif preprocessing_params[PreprocessingParam.SPL] == 3:
        if not splitting_file:
            raise ValueError("--splitting-file must be specified")

        splittings = io_utils.read_dict_from_2_columns(splitting_file, val_type=list, delim='|')
        ngramSplittingConfig.sc_splittings = splittings
        ngramSplittingConfig.set_splitting_type(NgramSplittingType.NUMBERS_AND_CUSTOM)
    elif preprocessing_params[PreprocessingParam.SPL] == 2:
        ngramSplittingConfig.set_splitting_type(NgramSplittingType.ONLY_NUMBERS)

    new_preprocessing_types_dict, got_pure_repr = calc_new_preprocessing_types_dict(old_preprocessing_params,
                                                                                    preprocessing_params)
    if old_preprocessing_params == new_preprocessing_types_dict:
        logger.warning("No new preprocessors to be applied found")
        exit(0)

    if got_pure_repr:
        logger.info("Representation resolved")
    else:
        logger.info(f"Representation not resolved: {new_preprocessing_types_dict}")
        logger.error(f"Partial representation is no longer supported")
        exit(388)

    gen_dir_name_from_verb_param = PrepParamsParser.encode_dict(new_preprocessing_types_dict)
    while os.path.exists(gen_dir_name_from_verb_param):
        gen_dir_name_from_verb_param += '_'

    full_dest_dir = os.path.join(dest_dir, REPR_EXTENSION, gen_dir_name_from_verb_param)
    full_metadata_dir = os.path.join(dest_dir, METADATA_DIR, gen_dir_name_from_verb_param)
    logger.info(f"Writing preprocessed files to {os.path.abspath(full_dest_dir)}")
    if not os.path.exists(full_dest_dir):
        os.makedirs(full_dest_dir)
    if not os.path.exists(full_metadata_dir):
        os.makedirs(full_metadata_dir)

    with open(os.path.join(full_dest_dir, 'preprocessing_types.json'), "w") as f:
        json.dump(new_preprocessing_types_dict, f)

    params = []
    for root, dirs, files in os.walk(full_src_dir):
        for file in files:
            if file.endswith(f".{PARSED_FILE_EXTENSION}"):

                full_dest_dir_with_sub_dir = os.path.join(full_dest_dir, os.path.relpath(root, full_src_dir))
                if not os.path.exists(full_dest_dir_with_sub_dir):
                    os.makedirs(full_dest_dir_with_sub_dir)
                params.append((os.path.join(root, file),
                               os.path.join(full_dest_dir_with_sub_dir, file),
                               preprocessing_params, old_preprocessing_params))
    files_total = len(params)
    current_file = 0
    start_time = time.time()
    with Pool() as pool:
        it = pool.imap_unordered(preprocess_and_write, params)
        for _ in it:
            current_file += 1
            logger.info(f"Processed {current_file} out of {files_total}")
            time_elapsed = time.time() - start_time
            logger.info(f"Time elapsed: {time_elapsed:.2f} s, estimated time until completion: "
                        f"{time_elapsed / current_file * files_total - time_elapsed:.2f} s")


if __name__ == '__main__':
    from logrec.properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_TO_REPR_ARGS

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--base-dir', action='store', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('dataset', action='store', help=f'path to the parsed dataset')
    parser.add_argument('-p', '--preprocessing-params', required=True, action='store',
                        help='preprocessing params line, \n Example: '
                             'enonly=1,nocomstr=0,spl=1,nosep=1,nonewlinestabs=0,nologs=0,')

    parser.add_argument('--bpe-base-repr', action='store', help='TODO')
    parser.add_argument('--bpe-n-merges', action='store', help='TODO')
    parser.add_argument('--splitting-file', action='store', help='Full path to the file with sc split words',
                        default=os.path.join(base_project_dir, 'splittings.txt'))

    args = parser.parse_known_args(*DEFAULT_TO_REPR_ARGS)
    args = args[0]

    run(args.base_dir, args.dataset, args.preprocessing_params, args.bpe_base_repr, args.bpe_n_merges,
        args.splitting_file)
