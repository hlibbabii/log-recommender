import json
import logging
import os
import re
from typing import List, Dict
from logrec.util.files import get_two_levels_subdirs

logger = logging.getLogger(__name__)

home_dir = os.environ["HOME"]

path_to_dup_jsons = ''  # TODO
base_raw_projects_dir = os.path.join(home_dir, 'raw_datasets/allamanis/nodup_en_only')


def build_name_to_name_in_split(base_raw_projects_dir: str):
    res = {}
    for dir, subdir, subsubdir in get_two_levels_subdirs(base_raw_projects_dir):
        repl = re.sub('^[0-9]*_', '', subsubdir)
        res[repl] = os.path.join(dir, subdir, subsubdir)
    return res


def convert_to_real_path(path: str, name_to_name_in_split: Dict[str, str]):
    return re.sub('^(.*?)/', lambda name: name_to_name_in_split[name.group(1)] + '/', path)


def process_dup_group(duplicate_group: List[str], name_to_name_in_split: Dict[str, str]):
    existing_real_paths = []
    for duplicate in duplicate_group:
        real_path = convert_to_real_path(duplicate, name_to_name_in_split)
        if os.path.exists(real_path):
            existing_real_paths.append(real_path)
    # TODO actually remove files
    return len(existing_real_paths) - 1


def run():
    logger.info("Loading json ...")
    dup_json = json.load(path_to_dup_jsons)

    logger.info("Matching json names to our names ...")
    name_to_name_in_split = build_name_to_name_in_split(base_raw_projects_dir)
    for name, name_in_split in name_to_name_in_split.items()[:5]:
        logger.info(f'{name} --> {name_in_split}')
    logger.info("...")

    n_files_removed_total = 0
    n_duplicated_files_total = 0
    for duplicate_group in dup_json:
        n_duplicated_files = len(duplicate_group)
        n_files_removed = process_dup_group(duplicate_group, name_to_name_in_split)
        logger.info(f'Duplicated files removed: {n_files_removed} out of {n_duplicated_files}')
        n_duplicated_files_total += n_duplicated_files
        n_files_removed_total += n_files_removed
    logger.info(f"Total duplicates removed: {n_files_removed_total} out of {n_duplicated_files_total}")


if __name__ == '__main__':
    run()
