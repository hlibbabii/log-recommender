import argparse
import gzip
import logging
import os
import pickle
import time
from multiprocessing.pool import Pool
from pathlib import Path

from logrec.dataprep.preprocessors import apply_preprocessors
from logrec.dataprep.preprocessors.general import from_file
from logrec.dataprep.preprocessors.preprocessing_types import PreprocessingParam
from logrec.dataprep.preprocess_params import pp_params
from logrec.infrastructure.fs import FS
from logrec.properties import DEFAULT_PARSE_PROJECTS_ARGS
from logrec.util.files import file_mapper

logger = logging.getLogger(__name__)

EXTENSION = "parsed"
FILENAMES_EXTENSION = "filenames"


def read_file_contents(file_path):
    with open(file_path, 'r') as f:
        try:
            return [line for line in f], file_path
        except UnicodeDecodeError:
            logger.error(f"Unicode decode error in file: {file_path}")


def preprocess_and_write(params):
    from logrec.properties import REWRITE_PARSED_FILE

    src_dir, dest_dir, train_test_valid, project, preprocessing_param_dict = params
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
        total_files = sum(f for f in file_mapper(dir_with_files_to_preprocess, lambda path: 1))
        logger.info(f"Preprocessing java files from {dir_with_files_to_preprocess}. Files to process: {total_files}")
        pickle.dump(preprocessing_param_dict, f, pickle.HIGHEST_PROTOCOL)
        for ind, (lines_from_file, file_path) in enumerate(
                file_mapper(dir_with_files_to_preprocess, read_file_contents)):
            if (ind+1) % 100 == 0:
                logger.info(
                    f"[{os.path.join(train_test_valid, project)}] Parsed {ind+1} out of {total_files} files ({(ind+1)/float(total_files)*100:.2f}%)")
            parsed = apply_preprocessors(from_file(lines_from_file), pp_params["preprocessors"], {
                'interesting_context_words': []
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


def run(dataset):
    fs = FS.for_parse_projects(dataset)

    logger.info(f"Getting files from {fs.path_to_raw_dataset}")
    logger.info(f"Writing preprocessed files to {fs.path_to_parsed_dataset}")
    preprocessing_types_dict = {k: None for k in PreprocessingParam}
    logger.info(f"To get preprocessing represantation, "
                f"resolve the following preprocessing params: {', '.join([pt.value for pt in PreprocessingParam])}")

    fs.save_pp_params(pp_params)
    fs.save_preprocessing_types(preprocessing_types_dict)

    params = []

    for train_test_valid, project in fs.get_raw_projects():
        params.append(
            (fs.path_to_raw_dataset, fs.path_to_parsed_dataset, train_test_valid, project, preprocessing_types_dict))

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


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('dataset', help='dataset name')

    args = parser.parse_known_args(*DEFAULT_PARSE_PROJECTS_ARGS)
    args = args[0]

    run(args.dataset)
