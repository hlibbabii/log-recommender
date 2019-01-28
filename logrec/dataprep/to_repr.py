import argparse
import gzip
import json
import logging
import os
import pickle
import time
from abc import ABCMeta, abstractmethod
from multiprocessing.pool import Pool
from typing import Optional, Dict

from logrec.dataprep import base_project_dir, METADATA_DIR, BPE_DIR, PARSED_DIR
from logrec.dataprep.preprocessors.general import to_token_list
from logrec.dataprep.prepparams import PreprocessingParam, get_types_to_be_repr, PrepParamsParser
from logrec.dataprep.preprocessors.repr import to_repr_list, ReprConfig
from logrec.dataprep.split.ngram import NgramSplittingType, NgramSplitConfig, SplitRepr
from logrec.dataprep.util import read_dict_from_2_columns
from logrec.properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_TO_REPR_ARGS

logger = logging.getLogger(__name__)

PARSED_FILE_EXTENSION = "parsed"
REPR_EXTENSION = "repr"
NOT_FINISHED_EXTENSION = "part"


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


def to_repr(preprocessing_params, token_list, n_gramm_splitting_config: Optional[NgramSplitConfig] = None):
    """
    Preprocesses token list according to given preprocessing params
    :param preprocessing_params: e.g. {
        PreprocessingType.EN_ONLY: 1,
        PreprocessingType.NO_COM_STR: 0,
        PreprocessingType.SPL: 4,
        PreprocessingType.NO_SEP: 0
        PreprocessingType.NO_NEWLINES_TABS: 0,
    }
    :param token_list: list of tokens to be preprocessed
    :return:
    """
    check_preprocessing_params_are_valid(preprocessing_params)
    types_to_be_repr = get_types_to_be_repr(preprocessing_params)
    splitRepr = SplitRepr.BONDERIES if preprocessing_params[PreprocessingParam.NO_SEP] else SplitRepr.BETWEEN_WORDS
    splitting_config = n_gramm_splitting_config or global_n_gramm_splitting_config
    repr_list = to_repr_list(token_list, ReprConfig(types_to_be_repr, splitting_config, splitRepr))
    return repr_list


def preprocess_and_write(params):
    src_file, dest_file, preprocessing_params = params
    if not os.path.exists(src_file):
        logger.error(f"File {src_file} does not exist")
        exit(2)

    logger.info(f"Preprocessing parsed file {src_file}")
    with gzip.GzipFile(src_file, 'rb') as i:
        preprocessing_param_dict = pickle.load(i)
        writer = FinalReprWriter(dest_file)

        if os.path.exists(writer.get_full_dest_name()):
            logger.warning(f"File {writer.get_full_dest_name()} already exists! Doing nothing.")
            return
        with writer as w:
            while True:
                try:
                    token_list = pickle.load(i)
                    repr = to_repr(preprocessing_params, token_list, global_n_gramm_splitting_config)
                    w.write(repr)
                except EOFError:
                    break
    # remove .part to show that all raw files in this chunk have been preprocessed
    os.rename(f'{writer.get_full_dest_name()}.{NOT_FINISHED_EXTENSION}', f'{writer.get_full_dest_name()}')


def init_splitting_config(dataset: str, preprocessing_params: Dict[str, int],
                          bpe_base_repr: Optional[str], bpe_n_merges: Optional[int], splitting_file: Optional[str]):
    global global_n_gramm_splitting_config
    global_n_gramm_splitting_config = NgramSplitConfig()
    if preprocessing_params[PreprocessingParam.SPL] in [4, 5, 6, 9]:
        if not bpe_base_repr:
            raise ValueError("--bpe-base-repr")

        if preprocessing_params[PreprocessingParam.SPL] == 9:
            if not bpe_n_merges:
                raise ValueError("--bpe-n-merges must be specified for repr **9**")
        else:
            bpe_n_merges_dict = {4: 5000, 5: 1000, 6: 10000}
            bpe_n_merges = bpe_n_merges_dict[preprocessing_params[PreprocessingParam.SPL]]

        if bpe_base_repr.find("/") == -1:
            bpe_base_dataset = dataset
        else:
            bpe_base_dataset, bpe_base_repr = bpe_base_repr.split("/")
        logger.info(f'Using bpe_n_merges: {bpe_n_merges}')
        path_to_merges_dir = os.path.join(DEFAULT_PARSED_DATASETS_DIR, bpe_base_dataset, METADATA_DIR, bpe_base_repr,
                                          BPE_DIR,
                                          str(bpe_n_merges))
        bpe_merges_file = os.path.join(path_to_merges_dir, 'merges.txt')
        bpe_merges_cache = os.path.join(path_to_merges_dir, 'merges_cache.txt')

        merges_cache = read_dict_from_2_columns(bpe_merges_cache, val_type=list)
        merges = []
        with open(bpe_merges_file, 'r') as f:
            for line in f:
                merges.append(line.rstrip('\n').split(' '))
        global_n_gramm_splitting_config.merges_cache = merges_cache
        global_n_gramm_splitting_config.merges = merges
        global_n_gramm_splitting_config.set_splitting_type(NgramSplittingType.BPE)
    elif preprocessing_params[PreprocessingParam.SPL] == 3:
        if not splitting_file:
            raise ValueError("--splitting-file must be specified")

        splittings = read_dict_from_2_columns(splitting_file, val_type=list, delim='|')
        global_n_gramm_splitting_config.sc_splittings = splittings
        global_n_gramm_splitting_config.set_splitting_type(NgramSplittingType.NUMBERS_AND_CUSTOM)
    elif preprocessing_params[PreprocessingParam.SPL] == 2:
        global_n_gramm_splitting_config.set_splitting_type(NgramSplittingType.ONLY_NUMBERS)


def run(dataset: str, preprocessing_params: str, bpe_base_repr: Optional[str],
        bpe_n_merges: Optional[int], splitting_file: Optional[str]):
    path_to_dataset = os.path.join(DEFAULT_PARSED_DATASETS_DIR, args.dataset)
    full_src_dir = os.path.join(path_to_dataset, PARSED_DIR)

    if not os.path.exists(full_src_dir):
        logger.error(f"Dir does not exist: {full_src_dir}")
        exit(3)
    logger.info(f"Reading parsed files from: {os.path.abspath(full_src_dir)}")

    preprocessing_params = PrepParamsParser.from_encoded_string(preprocessing_params)
    init_splitting_config(dataset, preprocessing_params, bpe_base_repr, bpe_n_merges, splitting_file)

    repr = PrepParamsParser.encode_dict(preprocessing_params)

    full_dest_dir = os.path.join(path_to_dataset, REPR_EXTENSION, repr)
    full_metadata_dir = os.path.join(path_to_dataset, METADATA_DIR, repr)
    logger.info(f"Writing preprocessed files to {os.path.abspath(full_dest_dir)}")
    if not os.path.exists(full_dest_dir):
        os.makedirs(full_dest_dir)
    if not os.path.exists(full_metadata_dir):
        os.makedirs(full_metadata_dir)

    with open(os.path.join(full_dest_dir, 'preprocessing_types.json'), "w") as f:
        json.dump(preprocessing_params, f)

    params = []
    for root, dirs, files in os.walk(full_src_dir):
        for file in files:
            if file.endswith(f".{PARSED_FILE_EXTENSION}"):

                full_dest_dir_with_sub_dir = os.path.join(full_dest_dir, os.path.relpath(root, full_src_dir))
                if not os.path.exists(full_dest_dir_with_sub_dir):
                    os.makedirs(full_dest_dir_with_sub_dir)
                params.append((os.path.join(root, file),
                               os.path.join(full_dest_dir_with_sub_dir, file),
                               preprocessing_params))
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
    parser = argparse.ArgumentParser()
    parser.add_argument('dataset', action='store', help=f'path to the parsed dataset')
    parser.add_argument('repr', action='store', help='preprocessing params line, \n Example: 10101')

    parser.add_argument('--bpe-base-repr', action='store', help='TODO')
    parser.add_argument('--bpe-n-merges', action='store', type=int, help='TODO')
    parser.add_argument('--splitting-file', action='store', help='Full path to the file with sc split words',
                        default=os.path.join(base_project_dir, 'splittings.txt'))

    args = parser.parse_known_args(*DEFAULT_TO_REPR_ARGS)
    args = args[0]

    run(args.dataset, args.repr, args.bpe_base_repr, args.bpe_n_merges, args.splitting_file)
