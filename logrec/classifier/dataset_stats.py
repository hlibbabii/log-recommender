import argparse
import logging
import re
from collections import defaultdict

from logrec.classifier.dataset_generator import LABEL_EXTENSION, CLASSIFICATION_DIR_NAME, CLASSIFICATION_TYPE, \
    get_dir_and_file
from logrec.dataprep.preprocessors.preprocessing_types import PrepParamsParser
from logrec.dataprep.util import merge_dicts_
from logrec.util.io_utils import file_mapper

PERCENT_OF_LOGGED_FILES_THRESHOLD = 7

WITH_LOGGING = "with_logging"
NO_LOGGING = "no logging"

logger = logging.getLogger(__name__)


def calc_logged_stats(path_to_label_file):
    stats = defaultdict(int)
    with open(path_to_label_file, 'r') as f:
        for line in f:
            stripped_line = line.rstrip('\n')
            if stripped_line == '1':
                stats[WITH_LOGGING] += 1
            elif stripped_line == '0':
                stats[NO_LOGGING] += 1
            else:
                raise AssertionError(f"Invalid line: {stripped_line} in file: {path_to_label_file}")
    if stats == {}:
        logger.warning(f"The project {path_to_label_file} contains no files. Ignoring...")
        return None
    else:
        return stats, re.sub(f"\.{LABEL_EXTENSION}$", "", get_dir_and_file(path_to_label_file))


def calc_stats(dest_dir):
    projects_to_ignore = []
    res_logged_stats = {}
    for logged_stats, proj_name in file_mapper(dest_dir, calc_logged_stats, LABEL_EXTENSION):
        if float(logged_stats[WITH_LOGGING]) / (logged_stats[WITH_LOGGING] + logged_stats[NO_LOGGING]) < (
                PERCENT_OF_LOGGED_FILES_THRESHOLD * 0.01):
            projects_to_ignore.append(proj_name)
        else:
            merge_dicts_(res_logged_stats, logged_stats)
    return projects_to_ignore, res_logged_stats


def run(dest_dir):
    projects_to_ignore, logged_stats = calc_stats(dest_dir)
    logger.info(f"Ignored projects: {projects_to_ignore}")
    logger.info(logged_stats)


if __name__ == '__main__':
    from logrec.local_properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_DATASET_GENERATOR_ARGS

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--base', action='store', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('dataset', action='store', help=f'path to the repr dataset')
    parser.add_argument('repr', action='store', help=f'path to the repr dataset')

    args = parser.parse_known_args(*DEFAULT_DATASET_GENERATOR_ARGS)
    args = args[0]

    clas9n_dataset_name = PrepParamsParser.to_classification_prep_params(args.repr)
    dest_dir = f'{args.base}/{args.dataset}/{CLASSIFICATION_DIR_NAME}/{CLASSIFICATION_TYPE}/{clas9n_dataset_name}'
    logger.info(f"Getting stats for {dest_dir}")

    run(dest_dir)
