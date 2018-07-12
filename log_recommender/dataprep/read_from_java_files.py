import argparse
import json
import logging
import os

from nn.preprocess_params import pp_params
from preprocessors import apply_preprocessors


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


def preprocess_and_write(dir, subdir, chunk):
    with open(os.path.join(dir, f'context.{chunk}.src'), 'w') as f:
        dir_with_files_to_preprocess=os.path.join(args.dir, subdir, chunk)
        logging.info(f"Preprocessing java files from {dir_with_files_to_preprocess}")
        total_files = sum([f for f in java_file_mapper(dir_with_files_to_preprocess, lambda path: 1)])
        print(f'Total amount of files to process: {total_files}')

        for ind, (lines_from_file, file_path) in enumerate(java_file_mapper(dir_with_files_to_preprocess, read_file_contents)):
            if len(lines_from_file) > pp_params['more_lines_ignore']:
                logging.debug(f"File {file_path} has {len(lines_from_file)} lines. Skiping...")
                continue
            logging.info(f"Processing file: {file_path} [{ind+1} out of {total_files}] containing {len(lines_from_file)} lines")
            processed = apply_preprocessors(lines_from_file, pp_params["preprocessors"], {'interesting_context_words': []})
            f.write(processed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fastai-input-file', action='store',
		default='/home/lv71161/hlibbabii/log-recommender/nn-data/devanbu_no_replaced_identifier_split_no_tabs_under_5000_15_percent/')
    parser.add_argument('--dir', action='store', default='/home/lv71161/hlibbabii/raw_datasets/devanbu/15_percent/')
    parser.add_argument('--folder', action='store')
    parser.add_argument('--chunk', action='store')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    dataset_dir = f'{args.fastai_input_file}'

    logging.info(f"Getting files from {os.path.abspath(args.dir)}")
    logging.info(f"Writing preprocessed files to {os.path.abspath(dataset_dir)}")

    train_dir = f'{dataset_dir}/train/'
    test_dir = f'{dataset_dir}/test/'
    if not os.path.exists(train_dir):
        os.makedirs(train_dir)
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    with open(f'{dataset_dir}/params.json', 'w') as f:
        json.dump(pp_params, f)
    if args.folder == 'train':
        preprocess_and_write(train_dir, "train/", args.chunk)
    else:
        preprocess_and_write(test_dir, "test/", args.chunk)

