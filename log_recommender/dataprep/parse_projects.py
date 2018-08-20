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
    src_dir, dest_dir, chunk, verbosity_param_dict = params
    path_to_preprocessed_file = os.path.join(dest_dir, f'preprocessed.{chunk}.parsed')
    if os.path.exists(path_to_preprocessed_file):
        logging.warning(f"File {path_to_preprocessed_file} already exists! Doing nothing.")
        exit(1)
    dir_with_files_to_preprocess = os.path.join(src_dir, chunk)
    if not os.path.exists(dir_with_files_to_preprocess):
        logging.error(f"Path {dir_with_files_to_preprocess} does not exist")
        exit(2)
    with open(f'{path_to_preprocessed_file}.part', 'wb') as f:
        logging.info(f"Preprocessing java files from {dir_with_files_to_preprocess}")
        total_files = sum([f for f in java_file_mapper(dir_with_files_to_preprocess, lambda path: 1)])
        print(f'Total amount of files to process: {total_files}')

        pickle.dump(verbosity_param_dict, f, pickle.HIGHEST_PROTOCOL)
        for ind, (lines_from_file, file_path) in enumerate(java_file_mapper(dir_with_files_to_preprocess, read_file_contents)):
            logging.info(f"Processing file: {file_path} [{ind+1} out of {total_files}] containing {len(lines_from_file)} lines")
            parsed = apply_preprocessors(lines_from_file, pp_params["preprocessors"], {
                'interesting_context_words': []
            })
            pickle.dump(parsed, f, pickle.HIGHEST_PROTOCOL)
    # remove .part to show that all raw files in this chunk have been preprocessed
    os.rename(f'{path_to_preprocessed_file}.part', path_to_preprocessed_file)


def split_two_last_levels(root):
    root = root + "/"
    return os.path.dirname(os.path.dirname(os.path.dirname(root))), Path(root).parts[-2], Path(root).parts[-1]


if __name__ == '__main__':
    base_from = f'{base_project_dir}/../raw_datasets/devanbu/'
    base_to = f'{base_project_dir}/nn-data/new_framework/'

    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-dataset', action='store', default='100_percent')
    parser.add_argument('--dest-dataset', action='store', default='100_percent')
    # parser.add_argument('--folder', action='store', default='train')
    # parser.add_argument('--chunk', action='store', default='1')
    parser.add_argument('--n-processes', action='store', default='32')
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

    with open(f'{dest_dataset_dir}/params.json', 'w') as f:
        json.dump(pp_params, f)
    with open(f'{dest_dataset_dir}/verbosity_params.json', 'w') as f:
        json.dump(verbosity_param_dict, f)

    params = []

    subfolder = "train"
    full_dest_dir = os.path.join(dest_dataset_dir, subfolder)
    if not os.path.exists(full_dest_dir):
        os.makedirs(full_dest_dir)
    for i in range(10000):
        params.append((os.path.join(raw_dataset_dir, subfolder), full_dest_dir, i+1, verbosity_param_dict))
    subfolder = "test"
    full_dest_dir = os.path.join(dest_dataset_dir, subfolder)
    if not os.path.exists(full_dest_dir):
        os.makedirs(full_dest_dir)
    for i in range(4000):
        params.append((os.path.join(raw_dataset_dir, subfolder), full_dest_dir, i + 1, verbosity_param_dict))
    subfolder = "valid"
    full_dest_dir = os.path.join(dest_dataset_dir, subfolder)
    if not os.path.exists(full_dest_dir):
        os.makedirs(full_dest_dir)
    for i in range(4000):
        params.append((os.path.join(raw_dataset_dir, subfolder), full_dest_dir, i + 1, verbosity_param_dict))

    files_total = len(params)
    current_file = 0
    start_time = time.time()
    with Pool(int(args.n_processes)) as pool:
        it = pool.imap_unordered(preprocess_and_write, params)
        for _ in it:
            current_file += 1
            logging.info(f"Processed {current_file} out of {files_total}")
            time_elapsed = time.time() - start_time
            logging.info(f"Time elapsed: {time_elapsed:.2f} s, estimated time until completion: "
                         f"{time_elapsed / current_file * files_total - time_elapsed:.2f} s")

