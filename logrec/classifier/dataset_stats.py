import argparse
import logging
import os
import re
from collections import defaultdict

from logrec.classifier.context_datasets import ContextsDataset, IGNORED_PROJECTS_FILE_NAME, get_dir_and_file
from logrec.classifier.log_position_classifier import CLASSIFICATION_TYPE
from logrec.dataprep.preprocessors.preprocessing_types import PrepParamsParser
from logrec.dataprep.util import merge_dicts_
from logrec.infrastructure.fs import CLASSIFICATION_DIR_NAME
from logrec.util import io_utils
from logrec.util.io_utils import file_mapper

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
        logger.warning(f"The project {path_to_label_file} contains no files. Skipping...")
        return None
    else:
        return stats, re.sub(f"\.{ContextsDataset.LABEL_FILE_EXT}$", "", get_dir_and_file(path_to_label_file))


def calc_stats(dest_dir, threshold):
    projects_to_ignore = []
    res_logged_stats = {}
    for logged_stats, proj_name in file_mapper(dest_dir, calc_logged_stats, ContextsDataset.LABEL_FILE_EXT):
        if float(logged_stats[WITH_LOGGING]) / (logged_stats[WITH_LOGGING] + logged_stats[NO_LOGGING]) <= (
                threshold * 0.01):
            projects_to_ignore.append(proj_name)
        else:
            merge_dicts_(res_logged_stats, logged_stats)
    return projects_to_ignore, res_logged_stats


def run(dest_dir, threshold):
    logger.info(f"Getting stats for {dest_dir}")
    logger.info(
        f"Ignoring projects where the percentage of file that contain logging is less than {threshold} %")
    projects_to_ignore, logged_stats = calc_stats(dest_dir, threshold)
    for i, p in enumerate(projects_to_ignore):
        logger.info(f"{i}: {p}")
    logger.info("")
    logger.info(logged_stats)
    output_file_path = os.path.join(dest_dir, f"{IGNORED_PROJECTS_FILE_NAME}.{threshold}")
    io_utils.dump_list(projects_to_ignore, output_file_path)
    logger.info(f"Ignored files with threshold {threshold} % were written to {output_file_path}")
    logger.info(f"Total ignored projects: {len(projects_to_ignore)}")


if __name__ == '__main__':
    from logrec.local_properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_DATASET_STATS_ARGS

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--base', action='store', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('dataset', action='store', help=f'dataset name')
    parser.add_argument('repr', action='store', help=f'repr name')
    parser.add_argument('threshold', action='store', help=f'threshold under which project is ignored')

    args = parser.parse_known_args(*DEFAULT_DATASET_STATS_ARGS)
    args = args[0]

    clas9n_dataset_name = PrepParamsParser.to_classification_prep_params(args.repr)
    dest_dir = os.path.join(args.base, args.dataset, CLASSIFICATION_DIR_NAME, CLASSIFICATION_TYPE, clas9n_dataset_name)

    run(dest_dir, float(args.threshold))
