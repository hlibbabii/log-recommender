import argparse
import json
import logging
import os
import pickle
import time
from abc import ABCMeta, abstractmethod
from multiprocessing.pool import Pool
from pickle import HIGHEST_PROTOCOL

from dataprep import base_project_dir
from dataprep.preprocessors.general import to_token_list
from dataprep.preprocessors.repr import to_repr
from dataprep.preprocessors.verbosity import token_to_verbosity_level_dict, verb_params_short_names

PARSED_FILE_EXTENSION = "parsed"
PART_REPR_EXTENSION = "partrepr"
REPR_EXTENSION = "repr"
NOT_FINISHED_EXTENSION = "part"


def calc_new_verbosity_param_dict(verbosity_param_dict, preprocessing_verbosity_params):
    if not isinstance(verbosity_param_dict, dict):
        raise AssertionError("Should be verbosity param dict!")
    new_verbosity_param_dict = {}
    for (k, v) in verbosity_param_dict.items():
        if v is None:
            new_verbosity_param_dict[k] = preprocessing_verbosity_params[k] if k in preprocessing_verbosity_params else None
        elif k in preprocessing_verbosity_params and preprocessing_verbosity_params[k] != v:
            raise ValueError(f'Preprocessing {k} has already been applied with value {v}. '
                            f'Cannot be applied again with value {preprocessing_verbosity_params[k]}')
        else:
            new_verbosity_param_dict[k] = v

    got_pure_repr = None not in new_verbosity_param_dict.values()
    return new_verbosity_param_dict, got_pure_repr


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


class IntermediateReprWriter(ReprWriter):
    def __init__(self, dest_file):
        super().__init__(dest_file, 'wb', f'{PART_REPR_EXTENSION}')

    def write(self, token_list):
        pickle.dump(token_list, self.handle, HIGHEST_PROTOCOL)


def preprocess_and_write(params):
    src_file, dest_file, preprocessing_verbosity_params, old_verbosity_params = params
    if not os.path.exists(src_file):
        logging.error(f"File {src_file} does not exist")
        exit(2)

    logging.info(f"Preprocessing parsed file {src_file}")
    with open(src_file, 'rb') as i:
        verbosity_param_dict = pickle.load(i)
        if old_verbosity_params != verbosity_param_dict:
            logging.error(f"File {src_file} was expected to have verbosity params "
                          f"{old_verbosity_params}, but has {verbosity_param_dict}")
            exit(221)
        new_verbosity_param_dict, got_pure_repr = calc_new_verbosity_param_dict(verbosity_param_dict, preprocessing_verbosity_params)
        writer = FinalReprWriter(dest_file) if got_pure_repr else IntermediateReprWriter(dest_file)

        if os.path.exists(writer.get_full_dest_name()):
            logging.warning(f"File {writer.get_full_dest_name()} already exists! Doing nothing.")
            return

        with writer as w:
            if not got_pure_repr:
                w.write(new_verbosity_param_dict)
            while True:
                try:
                    token_list = pickle.load(i)
                    repr = to_repr(preprocessing_verbosity_params, token_list)
                    w.write(repr)
                except EOFError:
                    break
    # remove .part to show that all raw files in this chunk have been preprocessed
    os.rename(f'{writer.get_full_dest_name()}.{NOT_FINISHED_EXTENSION}', f'{writer.get_full_dest_name()}')


def gen_dir_name(new_verbosity_param_dict, verb_params_short_names):
    yes = ""
    no = ""
    unknown = ""
    for (k,v) in new_verbosity_param_dict.items():
        if v is None:
            unknown += (verb_params_short_names[k] + "_unk_")
        elif v:
            yes += (verb_params_short_names[k] + "_1_")
        else:
            no += (verb_params_short_names[k] + "_0_")
    return (yes + no + unknown)[:-1]


if __name__ == '__main__':
    base_from = f'{base_project_dir}/nn-data/test/'
    base_to = f'{base_project_dir}/nn-data/test/'

    parser = argparse.ArgumentParser()
    parser.add_argument('--src-dir', action='store', default='test1/parsed')
    parser.add_argument('--dest-dir', action='store', default='test1')
    parser.add_argument('--verbosity-params', action='store', default='splitting_done=1,number_splitting_done=1,comments_str_literals_obfuscated=0,new_lines_and_tabs_removed=0,same_case_splitting=1')

    args = parser.parse_args()


    logging.basicConfig(level=logging.DEBUG)

    full_src_dir = f'{base_from}/{args.src_dir}'
    if not os.path.exists(full_src_dir):
        logging.error(f"Dir does not exist: {full_src_dir}")
        exit(3)
    logging.info(f"Reading parsed files from: {os.path.abspath(full_src_dir)}")
    with open(f'{full_src_dir}/verbosity_params.json', 'r') as f:
        old_verbosity_params = json.load(f)
    logging.info(f"Old verbosity params : {old_verbosity_params}")

    preprocessing_verbosity_params = {param.split('=')[0]: bool(int(param.split('=')[1])) for param in args.verbosity_params.split(',')}
    for param in preprocessing_verbosity_params.keys():
        if param not in token_to_verbosity_level_dict.values():
            raise ValueError(f"Invalid verbosity param: {param}")

    new_verbosity_param_dict, got_pure_repr = calc_new_verbosity_param_dict(old_verbosity_params,
                                                                            preprocessing_verbosity_params)
    if old_verbosity_params == new_verbosity_param_dict:
        logging.warning("No new preprocessors to be applied found")
        exit(0)

    if got_pure_repr:
        logging.info("Representation resolved")
    else:
        logging.info(f"Representation not resolved: {new_verbosity_param_dict}")

    gen_dir_name_from_verb_param = gen_dir_name(new_verbosity_param_dict, verb_params_short_names)
    while os.path.exists(gen_dir_name_from_verb_param):
        gen_dir_name_from_verb_param += '_'

    full_dest_dir = f'{base_to}/{args.dest_dir}/{"repr" if got_pure_repr else "partrepr"}/{gen_dir_name_from_verb_param}'
    logging.info(f"Writing preprocessed files to {os.path.abspath(full_dest_dir)}")
    if not os.path.exists(full_dest_dir):
        os.makedirs(full_dest_dir)

    with open(f'{full_dest_dir}/verbosity_params.json', "w") as f:
        json.dump(new_verbosity_param_dict, f)


    #TODO remove duplication
    files_total = 0
    for root, dirs, files in os.walk(full_src_dir):
        for file in files:
            if file.endswith(f".{PARSED_FILE_EXTENSION}") or file.endswith(f".{PART_REPR_EXTENSION}"):
                files_total += 1

    params = []
    for root, dirs, files in os.walk(full_src_dir):
        for file in files:
            if file.endswith(f".{PARSED_FILE_EXTENSION}") or file.endswith(f".{PART_REPR_EXTENSION}"):

                full_dest_dir_with_sub_dir = os.path.join(full_dest_dir, os.path.relpath(root, full_src_dir))
                if not os.path.exists(full_dest_dir_with_sub_dir):
                    os.makedirs(full_dest_dir_with_sub_dir)
                params.append((os.path.join(root, file),
                                     os.path.join(full_dest_dir_with_sub_dir, file),
                                     preprocessing_verbosity_params, old_verbosity_params))
    files_total = len(params)
    current_file = 0
    start_time = time.time()
    with Pool() as pool:
        it = pool.imap_unordered(preprocess_and_write, params)
        for _ in it:
            current_file += 1
            logging.info(f"Processed {current_file} out of {files_total}")
            time_elapsed = time.time() - start_time
            logging.info(f"Time elapsed: {time_elapsed:.2f} s, estimated time until completion: "
                         f"{time_elapsed / current_file * files_total - time_elapsed:.2f} s")
