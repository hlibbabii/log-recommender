import argparse
import logging
import os
import pickle
import time
from abc import ABCMeta, abstractmethod
from functools import reduce
from pickle import HIGHEST_PROTOCOL

from dataprep import base_project_dir
from dataprep.preprocessors.model.placeholders import placeholders
from dataprep.preprocessors.repr import to_repr
from dataprep.preprocessors.verbosity import token_to_verbosity_level_dict

PARSED_FILE_EXTENSION = "parsed"
PART_REPR_EXTENSION = "partrepr"
REPR_EXTENSION = "repr"
NOT_FINISHED_EXTENSION = "part"


def calc_new_verbosity_param_dict(verbosity_param_dict, preprocessing_verbosity_params):
    if not isinstance(verbosity_param_dict, dict):
        raise AssertionError("Should be verbosity param dict!")
    new_verbosity_param_dict = {k: (preprocessing_verbosity_params[k] if k in preprocessing_verbosity_params else v) for
                                (k, v) in verbosity_param_dict.items()}

    got_pure_repr = reduce(lambda a, b: a is not None and b is not None, new_verbosity_param_dict.values())
    return new_verbosity_param_dict, got_pure_repr


class ReprWriter(metaclass=ABCMeta):
    def __init__(self, dest_file, mode, extension):
        self.dest_file = dest_file
        self.mode = mode
        self.extension = extension

    def __enter__(self):
        self.handle = open(f'{self.dest_file}.{self.extension}.{NOT_FINISHED_EXTENSION}', self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.handle.close()

    @abstractmethod
    def write(self, token_list):
        '''Has to be implemented by subclasses'''


class FinalReprWriter(ReprWriter):
    def __init__(self, dest_file):
        super().__init__(dest_file, 'w', f'{REPR_EXTENSION}')

    def write(self, token_list):
        self.handle.write(repr(" ".join(map(lambda t : str(t) ,token_list))) + f" {placeholders['ect']}\n")


class IntermediateReprWriter(ReprWriter):
    def __init__(self, dest_file):
        super().__init__(dest_file, 'wb', f'{PART_REPR_EXTENSION}')

    def write(self, token_list):
        pickle.dump(token_list, self.handle, HIGHEST_PROTOCOL)


def preprocess_and_write(src_file, dest_file, preprocessing_verbosity_params):
    if os.path.exists(dest_file):
        logging.warning(f"File {dest_file} already exists! Doing nothing.")
        exit(1)
    if not os.path.exists(src_file):
        logging.error(f"File {src_file} does not exist")
        exit(2)

    start = time.time()
    logging.info(f"Preprocessing parsed file {src_file}")
    with open(src_file, 'rb') as i:
        verbosity_param_dict = pickle.load(i)
        new_verbosity_param_dict, got_pure_repr = calc_new_verbosity_param_dict(verbosity_param_dict, preprocessing_verbosity_params)
        writer = FinalReprWriter(dest_file) if got_pure_repr else IntermediateReprWriter(dest_file)

        with writer as w:
            if got_pure_repr:
                logging.info("Representation resolved")
            else:
                w.write(new_verbosity_param_dict)
                logging.info(f"Represenattion not resolved: {new_verbosity_param_dict}")
            while True:
                try:
                    token_list = pickle.load(i)
                    repr = to_repr(preprocessing_verbosity_params, token_list)
                    w.write(repr)
                except EOFError:
                    break
    # remove .part to show that all raw files in this chunk have been preprocessed
    os.rename(f'{dest_file}.{writer.extension}.{NOT_FINISHED_EXTENSION}', f'{dest_file}.{writer.extension}')
    logging.info(f"Preprocessed in {time.time() - start} seconds")

if __name__ == '__main__':
    base_from = f'{base_project_dir}/nn-data/test/parsed'
    base_to = f'{base_project_dir}/nn-data/test/repr'

    parser = argparse.ArgumentParser()
    parser.add_argument('--src-dir', action='store', default='test1')
    parser.add_argument('--dest-dir', action='store', default='test1')
    # parser.add_argument('--verbosity-params', action='store', default='new_lines_and_tabs_removed=1')
    parser.add_argument('--verbosity-params', action='store', default='splitting_done=1,number_splitting_done=1,comments_str_literals_obfuscated=1,new_lines_and_tabs_removed=1')
    args = parser.parse_args()
    #
    preprocessing_verbosity_params = {param.split('=')[0]: bool(int(param.split('=')[1])) for param in args.verbosity_params.split(',')}
    for param in preprocessing_verbosity_params.keys():
        if param not in token_to_verbosity_level_dict.values():
            raise ValueError(f"Invalid verbosity param: {param}")

    logging.basicConfig(level=logging.DEBUG)

    full_src_dir = f'{base_from}/{args.src_dir}'
    full_dest_dir = f'{base_to}/{args.dest_dir}'

    if not os.path.exists(full_src_dir):
        logging.error(f"Dir does not exist: {full_src_dir}")
        exit(3)
    logging.info(f"Reading parsed files from: {os.path.abspath(full_src_dir)}")
    logging.info(f"Writing preprocessed files to {os.path.abspath(full_dest_dir)}")

    if not os.path.exists(full_dest_dir):
        os.makedirs(full_dest_dir)

    import os
    for root, dirs, files in os.walk(full_src_dir):
        for file in files:
            if file.endswith(f".{PARSED_FILE_EXTENSION}") or file.endswith(f".{PART_REPR_EXTENSION}"):
                full_dest_dir_with_sub_dir = os.path.join(full_dest_dir, root[len(full_src_dir)+1:])
                if not os.path.exists(full_dest_dir_with_sub_dir):
                    os.makedirs(full_dest_dir_with_sub_dir)
                preprocess_and_write(os.path.join(root, file),
                                     os.path.join(full_dest_dir_with_sub_dir, file),
                                     preprocessing_verbosity_params)
                os.path.join(full_dest_dir, file)
