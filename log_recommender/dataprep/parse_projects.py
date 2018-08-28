import argparse
import json
import logging
import os
import pickle
import time
from multiprocessing.pool import Pool
from pathlib import Path

from dataprep import base_project_dir
from dataprep.preprocessors import apply_preprocessors
from dataprep.preprocessors.verbosity import get_all_verbosity_params
from nn.preprocess_params import pp_params


def get_two_levels_subdirs(dir):
    subdirs = next(os.walk(dir))[1]
    for subdir in subdirs:
        for subsubdir in next(os.walk(os.path.join(dir, subdir)))[1]:
            yield dir, subdir, subsubdir



def java_file_mapper(dir, func):
    import os
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(".java") and not file.startswith("."):
                ret = func(os.path.join(root, file))
                if ret is not None:
                    yield ret


def read_file_contents(file_path):
    with open(file_path, 'r') as f:
        try:
            return [line for line in f], file_path
        except UnicodeDecodeError:
            logging.error(f"Unicode decode error in file: {file_path}")


def preprocess_and_write(params):
    src_dir, dest_dir, subdir, chunk, verbosity_param_dict, splitting_file = params
    full_dest_dir = os.path.join(dest_dir, subdir)
    path_to_preprocessed_file = os.path.join(full_dest_dir, f'preprocessed.{chunk}.parsed')
    if not os.path.exists(full_dest_dir):
        os.makedirs(full_dest_dir, exist_ok=True)
    # if os.path.exists(path_to_preprocessed_file):
    #     logging.warning(f"File {path_to_preprocessed_file} already exists! Doing nothing.")
    #     return
    dir_with_files_to_preprocess = os.path.join(src_dir, subdir, chunk)
    if not os.path.exists(dir_with_files_to_preprocess):
        logging.error(f"Path {dir_with_files_to_preprocess} does not exist")
        exit(2)
    with open(f'{path_to_preprocessed_file}.part', 'wb') as f:
        total_files = sum([f for f in java_file_mapper(dir_with_files_to_preprocess, lambda path: 1)])
        logging.info(f"Preprocessing java files from {dir_with_files_to_preprocess}. Files to process: {total_files}")
        pickle.dump(verbosity_param_dict, f, pickle.HIGHEST_PROTOCOL)
        for ind, (lines_from_file, file_path) in enumerate(java_file_mapper(dir_with_files_to_preprocess, read_file_contents)):
            if (ind+1) % 100 == 0:
                logging.info(f"[{subdir}/{chunk}] Parsed {ind+1} out of {total_files} files ({(ind+1)/float(total_files)*100:.2f}%)")
            parsed = apply_preprocessors(lines_from_file, pp_params["preprocessors"], {
                'interesting_context_words': [],
                'splitting_file_location': splitting_file
            })
            pickle.dump(parsed, f, pickle.HIGHEST_PROTOCOL)
    # remove .part to show that all raw files in this chunk have been preprocessed
    os.rename(f'{path_to_preprocessed_file}.part', path_to_preprocessed_file)


def split_two_last_levels(root):
    root = root + "/"
    return os.path.dirname(os.path.dirname(os.path.dirname(root))), Path(root).parts[-2], Path(root).parts[-1]


if __name__ == '__main__':
    base_from = f'{base_project_dir}/nn-data/'
    base_to = f'{base_project_dir}/nn-data//'

    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-dataset', action='store', default='test/raw/test1')
    parser.add_argument('--dest-dataset', action='store', default='test/test1')
    # parser.add_argument('--folder', action='store', default='train')
    # parser.add_argument('--chunk', action='store', default='1')
    parser.add_argument('--splitting-file', action='store',
                        default='/home/hlib/thesis/log-recommender/nn-data/devanbu_split_no_tabs_under_2000/splits/split.txt')
    # parser.add_argument('--n-processes', action='store', default='1')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    raw_dataset_dir=f'{base_from}/{args.raw_dataset}/'
    dest_dataset_dir = f'{base_to}/{args.dest_dataset}/parsed/'

    logging.info(f"Getting files from {os.path.abspath(raw_dataset_dir)}")
    logging.info(f"Writing preprocessed files to {os.path.abspath(dest_dataset_dir)}")
    verbosity_params = get_all_verbosity_params()
    verbosity_param_dict = {k:None for k in verbosity_params}
    logging.info(f"To get preprocessing represantation, "
                 f"resolve the following verbosity params: {verbosity_params}")

    if not os.path.exists(dest_dataset_dir):
        os.makedirs(dest_dataset_dir)
    with open(f'{dest_dataset_dir}/params.json', 'w') as f:
        json.dump(pp_params, f)
    with open(f'{dest_dataset_dir}/verbosity_params.json', 'w') as f:
        json.dump(verbosity_param_dict, f)

    params = []

    for _, subdir, chunk in get_two_levels_subdirs(raw_dataset_dir):
        params.append((raw_dataset_dir, dest_dataset_dir, subdir, chunk, verbosity_param_dict, args.splitting_file))

    files_total = len(params)
    current_file = 0
    start_time = time.time()
    with Pool() as pool:
        it = pool.imap_unordered(preprocess_and_write, params)
        for _ in it:
            current_file += 1
            logging.info(f"Processed {current_file} out of {files_total} chunks")
            time_elapsed = time.time() - start_time
            logging.info(f"Time elapsed: {time_elapsed:.2f} s, estimated time until completion: "
                         f"{time_elapsed / current_file * files_total - time_elapsed:.2f} s")

