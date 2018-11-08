import argparse
import gzip
import json
import logging
import os
import pickle
import time
from multiprocessing.pool import Pool
from pathlib import Path

from logrec.dataprep import base_project_dir
from logrec.dataprep.preprocessors import apply_preprocessors
from logrec.dataprep.preprocessors.preprocessing_types import PreprocessingType
from logrec.dataprep.preprocess_params import pp_params

logger = logging.getLogger(__name__)

EXTENSION = "parsed"
FILENAMES_EXTENSION = "filenames"


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
            logger.error(f"Unicode decode error in file: {file_path}")


def preprocess_and_write(params):
    from logrec.local_properties import REWRITE_PARSED_FILE

    src_dir, dest_dir, train_test_valid, project, preprocessing_param_dict, splitting_file = params
    full_dest_dir = os.path.join(dest_dir, train_test_valid)
    path_to_preprocessed_file = os.path.join(full_dest_dir, f'{project}.{EXTENSION}')
    if not os.path.exists(full_dest_dir):
        os.makedirs(full_dest_dir, exist_ok=True)
    if not REWRITE_PARSED_FILE and os.path.exists(path_to_preprocessed_file):
        logger.warning(f"File {path_to_preprocessed_file} already exists! Doing nothing.")
        return
    dir_with_files_to_preprocess = os.path.join(src_dir, train_test_valid, project)
    if not os.path.exists(dir_with_files_to_preprocess):
        logger.error(f"Path {dir_with_files_to_preprocess} does not exist")
        exit(2)
    filenames=[]
    with gzip.GzipFile(f'{path_to_preprocessed_file}.part', 'wb') as f:
        total_files = sum([f for f in java_file_mapper(dir_with_files_to_preprocess, lambda path: 1)])
        logger.info(f"Preprocessing java files from {dir_with_files_to_preprocess}. Files to process: {total_files}")
        pickle.dump(preprocessing_param_dict, f, pickle.HIGHEST_PROTOCOL)
        for ind, (lines_from_file, file_path) in enumerate(java_file_mapper(dir_with_files_to_preprocess, read_file_contents)):
            if (ind+1) % 100 == 0:
                logger.info(
                    f"[{train_test_valid}/{project}] Parsed {ind+1} out of {total_files} files ({(ind+1)/float(total_files)*100:.2f}%)")
            parsed = apply_preprocessors(lines_from_file, pp_params["preprocessors"], {
                'interesting_context_words': [],
                'splitting_file_location': splitting_file
            })
            pickle.dump(parsed, f, pickle.HIGHEST_PROTOCOL)
            filename=os.path.relpath(file_path, start=dir_with_files_to_preprocess)
            filenames.append(filename)

    with open(os.path.join(full_dest_dir, f'.{project}.{FILENAMES_EXTENSION}'), "w") as f:
        for filename in filenames:
            f.write(f"{filename}\n")

    # remove .part to show that all raw files in this project have been preprocessed
    os.rename(f'{path_to_preprocessed_file}.part', path_to_preprocessed_file)


def split_two_last_levels(root):
    root = root + "/"
    return os.path.dirname(os.path.dirname(os.path.dirname(root))), Path(root).parts[-2], Path(root).parts[-1]


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    from logrec.local_properties import DEFAULT_RAW_DATASETS_DIR, DEFAULT_PARSED_DATASETS_DIR, \
        DEFAULT_PARSE_PROJECTS_ARGS

    parser = argparse.ArgumentParser()
    parser.add_argument('--base-from',action='store', default=DEFAULT_RAW_DATASETS_DIR)
    parser.add_argument('--base-to',action='store', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('src', help="name of the 'raw' dataset")
    parser.add_argument('dest', help='destination for parsed files, recommended format <dataset name>/parsed')
    parser.add_argument('--splitting-file', action='store',
                        default=f'{base_project_dir}/splittings.txt')
    args = parser.parse_known_args(*DEFAULT_PARSE_PROJECTS_ARGS)
    args = args[0]

    raw_dataset_dir=f'{args.base_from}/{args.src}/'
    dest_dataset_dir = f'{args.base_to}/{args.dest}/'

    logger.info(f"Getting files from {os.path.abspath(raw_dataset_dir)}")
    logger.info(f"Writing preprocessed files to {os.path.abspath(dest_dataset_dir)}")
    preprocessing_types_dict = {k: None for k in PreprocessingType}
    logger.info(f"To get preprocessing represantation, "
                 f"resolve the following preprocessing params: {', '.join([pt.value for pt in PreprocessingType])}")

    if not os.path.exists(dest_dataset_dir):
        os.makedirs(dest_dataset_dir)
    with open(f'{dest_dataset_dir}/params.json', 'w') as f:
        json.dump(pp_params, f)
    with open(f'{dest_dataset_dir}/preprocessing_types.json', 'w') as f:
        json.dump(preprocessing_types_dict, f)

    params = []

    for _, train_test_valid, project in get_two_levels_subdirs(raw_dataset_dir):
        params.append((raw_dataset_dir, dest_dataset_dir, train_test_valid, project, preprocessing_types_dict, args.splitting_file))

    files_total = len(params)
    current_file = 0
    start_time = time.time()
    with Pool() as pool:
        it = pool.imap_unordered(preprocess_and_write, params)
        for _ in it:
            current_file += 1
            logger.info(f"Processed {current_file} out of {files_total} chunks")
            time_elapsed = time.time() - start_time
            logger.info(f"Time elapsed: {time_elapsed:.2f} s, estimated time until completion: "
                         f"{time_elapsed / current_file * files_total - time_elapsed:.2f} s")

