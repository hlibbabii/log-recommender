import argparse
import gzip
import logging
import os
import pickle
from abc import ABCMeta, abstractmethod
from multiprocessing.pool import Pool
from typing import Optional, List

import jsons
from tqdm import tqdm

from logrec.dataprep import base_project_dir, METADATA_DIR, BPE_DIR, PARSED_DIR
from logrec.dataprep.preprocessors.general import to_token_list
from logrec.dataprep.prepconfig import PrepParam, get_types_to_be_repr, PrepConfig
from logrec.dataprep.preprocessors.repr import to_repr_list, ReprConfig
from logrec.dataprep.split.bpe_encode import read_merges
from logrec.dataprep.split.ngram import NgramSplittingType, NgramSplitConfig
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


def get_global_n_gramm_splitting_config():
    return global_n_gramm_splitting_config


def to_repr(prep_config: PrepConfig, token_list: List, n_gramm_splitting_config: Optional[NgramSplitConfig] = None):
    types_to_be_repr = get_types_to_be_repr(prep_config)
    splitting_config = n_gramm_splitting_config or get_global_n_gramm_splitting_config()
    dict_based_non_eng = (prep_config.get_param_value(PrepParam.EN_ONLY) != 3)
    lowercase = (prep_config.get_param_value(PrepParam.CAPS) == 1)
    repr_list = to_repr_list(token_list, ReprConfig(types_to_be_repr, splitting_config, dict_based_non_eng, lowercase))
    return repr_list


def preprocess_and_write(params):
    src_file, dest_file, prep_config = params
    if not os.path.exists(src_file):
        logger.error(f"File {src_file} does not exist")
        exit(2)

    logger.debug(f"Preprocessing parsed file {src_file}")
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
                    repr = to_repr(prep_config, token_list, global_n_gramm_splitting_config)
                    w.write(repr)
                except EOFError:
                    break
    # remove .part to show that all raw files in this chunk have been preprocessed
    os.rename(f'{writer.get_full_dest_name()}.{NOT_FINISHED_EXTENSION}', f'{writer.get_full_dest_name()}')


def init_splitting_config(dataset: str, prep_config: PrepConfig,
                          bpe_base_repr: Optional[str], bpe_n_merges: Optional[int], splitting_file: Optional[str], merges_file):
    global global_n_gramm_splitting_config
    global_n_gramm_splitting_config = NgramSplitConfig()
    if prep_config.get_param_value(PrepParam.SPLIT) in [4, 5, 6, 7, 8, 9]:
        if merges_file:
            logger.info(f'Using bpe merges file: {merges_file}')
            global_n_gramm_splitting_config.merges_cache = []
            global_n_gramm_splitting_config.merges = read_merges(merges_file)
        else:
            if not bpe_base_repr:
                bpe_base_repr = prep_config.get_base_bpe_prep_config()

            if prep_config.get_param_value(PrepParam.SPLIT) == 9:
                if not bpe_n_merges:
                    raise ValueError("--bpe-n-merges must be specified for repr **9**")
            else:
                bpe_n_merges_dict = {4: 5000, 5: 1000, 6: 10000, 7: 20000, 8: 0}
                bpe_n_merges = bpe_n_merges_dict[prep_config.get_param_value(PrepParam.SPLIT)]

            if bpe_base_repr.find("/") == -1:
                bpe_base_dataset = dataset
            else:
                bpe_base_dataset, bpe_base_repr = bpe_base_repr.split("/")
            logger.info(f'Using bpe base dataset: {bpe_base_dataset}')
            logger.info(f'Using bpe base repr: {bpe_base_repr}')
            logger.info(f'Using bpe_n_merges: {bpe_n_merges}')
            path_to_merges_dir = os.path.join(DEFAULT_PARSED_DATASETS_DIR, bpe_base_dataset, METADATA_DIR, bpe_base_repr,
                                              BPE_DIR,
                                              str(bpe_n_merges))
            bpe_merges_file = os.path.join(path_to_merges_dir, 'merges.txt')
            bpe_merges_cache = os.path.join(path_to_merges_dir, 'merges_cache.txt')

            global_n_gramm_splitting_config.merges_cache = read_dict_from_2_columns(bpe_merges_cache, val_type=list)
            global_n_gramm_splitting_config.merges = read_merges(bpe_merges_file)
        global_n_gramm_splitting_config.set_splitting_type(NgramSplittingType.BPE)
    elif prep_config.get_param_value(PrepParam.SPLIT) == 3:
        if not splitting_file:
            raise ValueError("--splitting-file must be specified")

        splittings = read_dict_from_2_columns(splitting_file, val_type=list, delim='|')
        global_n_gramm_splitting_config.sc_splittings = splittings
        global_n_gramm_splitting_config.set_splitting_type(NgramSplittingType.NUMBERS_AND_CUSTOM)
    elif prep_config.get_param_value(PrepParam.SPLIT) == 2:
        global_n_gramm_splitting_config.set_splitting_type(NgramSplittingType.ONLY_NUMBERS)


def run(dataset: str, preprocessing_params: str, bpe_base_repr: Optional[str],
        bpe_n_merges: Optional[int], splitting_file: Optional[str], merges_file):
    path_to_dataset = os.path.join(DEFAULT_PARSED_DATASETS_DIR, args.dataset)
    full_src_dir = os.path.join(path_to_dataset, PARSED_DIR)

    if not os.path.exists(full_src_dir):
        logger.error(f"Dir does not exist: {full_src_dir}")
        exit(3)
    logger.info(f"Reading parsed files from: {os.path.abspath(full_src_dir)}")

    preprocessing_params = PrepConfig.from_encoded_string(preprocessing_params)
    init_splitting_config(dataset, preprocessing_params, bpe_base_repr, bpe_n_merges, splitting_file, merges_file)

    repr = str(preprocessing_params)

    full_dest_dir = os.path.join(path_to_dataset, REPR_EXTENSION, repr)
    full_metadata_dir = os.path.join(path_to_dataset, METADATA_DIR, repr)
    logger.info(f"Writing preprocessed files to {os.path.abspath(full_dest_dir)}")
    if not os.path.exists(full_dest_dir):
        os.makedirs(full_dest_dir)
    if not os.path.exists(full_metadata_dir):
        os.makedirs(full_metadata_dir)

    with open(os.path.join(full_dest_dir, 'preprocessing_types.json'), "w") as f:
        json_str = jsons.dumps(preprocessing_params)
        f.write(json_str)

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
    with Pool() as pool:
        it = pool.imap_unordered(preprocess_and_write, params)
        for _ in tqdm(it, total=files_total):
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dataset', action='store', help=f'path to the parsed dataset')
    parser.add_argument('repr', action='store', help='preprocessing params line, \n Example: 101011')
    parser.add_argument('--merges-file', action='store')

    parser.add_argument('--bpe-base-repr', action='store', help='TODO')
    parser.add_argument('--bpe-n-merges', action='store', type=int, help='TODO')
    parser.add_argument('--splitting-file', action='store', help='Full path to the file with sc split words',
                        default=os.path.join(base_project_dir, 'splittings.txt'))

    args = parser.parse_known_args(*DEFAULT_TO_REPR_ARGS)
    args = args[0]

    run(args.dataset, args.repr, args.bpe_base_repr, args.bpe_n_merges, args.splitting_file, args.merges_file)
