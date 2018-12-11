import json
import os
from collections import defaultdict

import deepdiff

PARAM_FILE_NAME = 'params.json'
DEEPDIFF_ADDED = 'dictionary_item_added'
DEEPDIFF_REMOVED = 'dictionary_item_removed'
DEEPDIFF_CHANGED = 'values_changed'


def find_most_similar_config(percent_prefix, path_to_dataset, current_config):
    config_diff_dict = defaultdict(list)
    for (dirpath, dirnames, filenames) in os.walk(path_to_dataset):
        for dirname in dirnames:
            if not dirname.startswith(percent_prefix):
                continue
            file_path = os.path.join(dirpath, dirname, PARAM_FILE_NAME)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    config = json.load(f)
                config_diff = deepdiff.DeepDiff(config, current_config)
                if config_diff == {}:
                    return dirname, {}
                else:
                    n_changed_params = (len(config_diff[DEEPDIFF_ADDED]) if DEEPDIFF_ADDED in config_diff else 0) \
                                       + (len(config_diff[DEEPDIFF_CHANGED]) if DEEPDIFF_CHANGED in config_diff else 0) \
                                       + (len(config_diff[DEEPDIFF_REMOVED]) if DEEPDIFF_REMOVED in config_diff else 0)
                    config_diff_dict[n_changed_params].append((dirname, config_diff))
    if not config_diff_dict:
        return None, deepdiff.DeepDiff({}, current_config)
    else:
        return config_diff_dict[min(config_diff_dict)][-1]


def extract_last_key(keys):
    last_apostrophe = keys.rindex('\'')
    return keys[keys[:last_apostrophe].rindex('\'') + 1:last_apostrophe]


def find_name_for_new_config(percent_prefix, config_diff):
    name = ""
    if DEEPDIFF_CHANGED in config_diff:
        for key, val in config_diff[DEEPDIFF_CHANGED].items():
            name += extract_last_key(key)
            name += "_"
            name += str(val['new_value'])
            name += "_"
    if DEEPDIFF_ADDED in config_diff:
        for key in config_diff[DEEPDIFF_ADDED]:
            name += extract_last_key(key)
            name += "_"
    if DEEPDIFF_REMOVED in config_diff:
        for key in config_diff[DEEPDIFF_REMOVED]:
            name += extract_last_key(key)
            name += "_"
    if name:
        name = name[:-1]
    return f'{percent_prefix}{name}'
