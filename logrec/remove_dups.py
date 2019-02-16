import json
import logging
import os
import re
from typing import List, Dict
from logrec.util.files import get_two_levels_subdirs

logger = logging.getLogger(__name__)

home_dir = os.environ["HOME"]

path_to_dup_jsons = os.path.join(home_dir, 'log-recommender-master', 'java-github-duplicates.json')
base_raw_projects_dir = os.path.join(home_dir, 'raw_datasets/allamanis/nodup_all')


def build_name_to_name_in_split(base_raw_projects_dir: str):
    res = {}
    for dir, subdir, subsubdir in get_two_levels_subdirs(base_raw_projects_dir):
        repl = re.sub('^[0-9]*_', '', subsubdir)
        res[repl] = os.path.join(dir, subdir, subsubdir)
    return res

NON_EXISTING_PATH=os.path.join(home_dir, 'this_path_will_never_exist')

def convert_to_real_split_path(path: str, name_to_name_in_split: Dict[str, str]):
    return re.sub('^(.*?)/', lambda name: (name_to_name_in_split[name.group(1)] if name.group(1) in name_to_name_in_split else NON_EXISTING_PATH) + '/', path)


def convert_to_real_path(path: str, name_to_name_in_split: Dict[str, str]):
    return os.path.join(base_raw_projects_dir, path)

def process_dup_group(duplicate_group: List[str], name_to_real_name: Dict[str, str]):
    existing_real_paths = []
    for duplicate in duplicate_group:
        real_path = convert_to_real_path(duplicate, name_to_real_name)
        if os.path.exists(real_path):
            existing_real_paths.append(real_path)
    for file in existing_real_paths[1:]:
        logger.info(f"Removing: {file}...")
        os.remove(file)
    return len(existing_real_paths) - 1 if len(existing_real_paths) > 0 else 0


def run():
    logger.info("Loading json ...")
    with open(path_to_dup_jsons, 'r') as f:
        dup_json = json.load(f)

    #logger.info("Matching json names to our names ...")
    #name_to_real_name = build_name_to_name_in_split(base_raw_projects_dir)
    #for i, (name, name_in_split) in enumerate(name_to_real_name.items()):
    #    logger.info(f'{name} --> {name_in_split}')
    #    if i == 5: break
    #logger.info("...")
    name_to_real_name=None

    n_files_removed_total = 0
    n_duplicated_files_total = 0
    total_groups = len(dup_json)
    for i, duplicate_group in enumerate(dup_json):
        logger.info(f"Processing duplication group {i} out of {total_groups} ...")
        n_duplicated_files = len(duplicate_group) - 1
        n_files_removed = process_dup_group(duplicate_group, name_to_real_name)
        logger.info(f'Duplicated files removed: {n_files_removed} out of {n_duplicated_files}')
        n_duplicated_files_total += n_duplicated_files
        n_files_removed_total += n_files_removed
    logger.info(f"Total duplicates removed: {n_files_removed_total} out of {n_duplicated_files_total}")


if __name__ == '__main__':
    run()
