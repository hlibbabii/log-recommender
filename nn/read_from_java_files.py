import argparse
import json
import logging
import os

from preprocess_params import pp_params
from write_for_external import process_full_identifiers


def java_file_mapper(dir, func):
    import os
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(".java"):
                ret = func(os.path.join(root, file))
                if ret is not None:
                    yield ret


def read_file_contents(file_path):
    with open(file_path, 'r') as f:
        try:
            return [line for line in f], file_path
        except UnicodeDecodeError:
            logging.error(f"Unicode decode error in file: {file_path}")


def preprocess_and_write(dir, subdir, chunks):
    total_files = sum([f for f in java_file_mapper(os.path.join(args.dir, subdir), lambda path: 1)])
    print(f'Total amount of files to process: {total_files}')

    with open(os.path.join(dir, f'context.0.src'), 'w') as f0, \
            open(os.path.join(dir, f'context.1.src'), 'w') as f1: #TODO loop!
        for ind, (lines_from_file, file_path) in enumerate(
                java_file_mapper(os.path.join(args.dir, subdir), read_file_contents)):
            if len(lines_from_file) > pp_params['more_lines_ignore']:
                logging.debug(f"File {file_path} has {len(lines_from_file)} lines. Skiping...")
                continue
            logging.info(f"Processing file: {file_path} [{ind} out of {total_files}] containing {len(lines_from_file)} lines")
            processed = process_full_identifiers(lines_from_file, pp_params["preprocessors"], [])
            if ind % 2 == 0:
                f0.write(processed)
            else:
                f1.write(processed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fastai-input-file', action='store',
                        default='../nn-data/devanbu_no_replaced_identifier_split_no_tabs_under_2000/')
    parser.add_argument('--dir', action='store', default='../../FSE\'17 Replication/projects/1_percent/')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    dataset_dir = f'{args.fastai_input_file}'
    train_dir = f'{dataset_dir}/train/'
    test_dir = f'{dataset_dir}/test/'
    if not os.path.exists(train_dir):
        os.makedirs(train_dir)
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    with open(f'{dataset_dir}/params.json', 'w') as f:
        json.dump(pp_params, f)
    preprocess_and_write(train_dir, "Train/", 2)
    preprocess_and_write(test_dir, "Test/", 2)

