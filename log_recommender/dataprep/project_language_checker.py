import argparse
import logging
import math
import os
from collections import defaultdict

from dataprep import base_project_dir
from dataprep.lcsplitting.lowercase_words_splitter import load_english_dict
from dataprep.preprocessors.noneng import isascii

DEFAULT_MIN_FREQ_TO_BE_NON_ENG = 0.01
DEFAULT_MIN_WORDS_TO_BE_NON_ENG = 5
DEFAULT_MIN_CHARS_TO_BE_NON_ENG=4


def create_word_to_lang_map(dicts_dir, english_general_dict):
    dict_files_names = [f for f in os.listdir(dicts_dir)]
    word_to_lang_map = defaultdict(set)
    for dict_file_name in dict_files_names:
        with open(os.path.join(dicts_dir,dict_file_name), 'r') as f:
            for line in f:
                word = line.split('/')[0]
                if word not in english_general_dict and len(word) >= DEFAULT_MIN_CHARS_TO_BE_NON_ENG:
                    word_to_lang_map[word].add(dict_file_name.split(".")[0])
    word_to_lang_map.default_factory = None
    return word_to_lang_map


def calc_lang_stats(file, word_to_lang_map):
    lang_to_number = defaultdict(int)
    lang_to_word_examples = defaultdict(list)
    encountered_words = set()
    total = 0
    with open(file, 'r') as f:
        for line in f:
            for word in line.split():
                if word not in encountered_words:
                    total += 1
                    encountered_words.add(word)
                    if not isascii(word):
                        lang_to_number['nonascii'] +=1
                        lang_to_word_examples['nonascii'].append(word)
                    if word in word_to_lang_map:
                        langs_word_belongs_to = word_to_lang_map[word]
                        for lang in langs_word_belongs_to:
                            lang_to_number[lang] += 1
                            lang_to_word_examples[lang].append(word)

    lang_to_percent = {k: float(v) / total if total > 0 else 0 for k, v in lang_to_number.items()}
    return lang_to_percent, lang_to_word_examples, total


def check_more_than_limit(lang_to_percent, total):
    for v in lang_to_percent.values():
        if v > min_freq_to_be_non_eng and total * v > min_words_to_be_non_eng:
            return True
    return False

def gen_stats(lang_to_percent_list):
    gr = defaultdict(int)
    for lang_to_percent in lang_to_percent_list:
        max_percent = max(lang_to_percent.values()) if lang_to_percent else .0
        gr[math.ceil(max_percent*100)] += 1
    gr.default_factory = None
    return gr


if __name__ == '__main__':
    default_base_dataset_dir = f'{base_project_dir}/nn-data/new_framework/'

    parser = argparse.ArgumentParser()
    parser.add_argument('--min-freq', type=float, default=f'{DEFAULT_MIN_FREQ_TO_BE_NON_ENG}')
    parser.add_argument('--min-words', type=int, default=f'{DEFAULT_MIN_WORDS_TO_BE_NON_ENG}')
    parser.add_argument('--min-chars', type=int, default=f'{DEFAULT_MIN_CHARS_TO_BE_NON_ENG}')
    parser.add_argument('--base-dataset-dir', default=f'{default_base_dataset_dir}')
    parser.add_argument('preprocessed_dataset', help='path to preprocessed dataset relative '
                                                     'to the one passed as --base-dataset-dir param')

    args = parser.parse_args()

    min_freq_to_be_non_eng = args.min_freq
    min_words_to_be_non_eng = args.min_words
    min_chars_to_be_non_eng = args.min_chars

    path_to_dicts = f"{base_project_dir}/dicts/"
    path_to_non_eng_dicts = f"{path_to_dicts}/non-eng"
    path_to_general_english_dict = f'{path_to_dicts}/eng'

    path_to_dir_with_preprocessed_projects = f'{args.base_dataset_dir}/{args.preprocessed_dataset}'

    logging.basicConfig(level=logging.DEBUG)
    if not os.path.exists(path_to_dir_with_preprocessed_projects):
        logging.error(f"Path: {path_to_dir_with_preprocessed_projects} does not exist")
        exit(1)

    logging.info("Loading english dictionary")
    english_general_dict = load_english_dict(path_to_general_english_dict)
    logging.info("Loading non-english dictionaries")
    word_to_lang_map = create_word_to_lang_map(path_to_non_eng_dicts, english_general_dict)

    non_english_files = []
    all_files = []
    for file in os.listdir(path_to_dir_with_preprocessed_projects):
        lang_to_percent, lang_to_word_examples, total = \
            calc_lang_stats(os.path.join(path_to_dir_with_preprocessed_projects, file), word_to_lang_map)
        non_eng = check_more_than_limit(lang_to_percent, total)
        all_files.append((file, lang_to_percent, total, lang_to_word_examples))
        if non_eng:
            non_english_files.append((file, lang_to_percent, total, lang_to_word_examples))
            print(f'Gen stats: file:{file}, {lang_to_percent}, total: {total}')
            print(lang_to_word_examples)
            print("\n\n")
    non_english_files.sort(key=lambda x: max(x[1].values()) if x[1] else 0.0)
    with open(f'{path_to_dir_with_preprocessed_projects}/noneng_projects_{min_freq_to_be_non_eng}_{min_words_to_be_non_eng}_{min_chars_to_be_non_eng}.txt', 'w') as f:
        for file, _, _, _ in non_english_files:
            f.write(file + "\n")

    with open(f'{path_to_dir_with_preprocessed_projects}/noneng_projects_verbose_{min_freq_to_be_non_eng}_{min_words_to_be_non_eng}_{min_chars_to_be_non_eng}.txt', 'w') as f:
        for file, lang_to_percent, total, lang_to_word_examples in non_english_files:
            f.write(f'Gen stats: file:{file}, {lang_to_percent}, total: {total}\n')
            f.write(f"{lang_to_word_examples}\n")
            f.write("\n\n")
    stats = gen_stats(list(map(lambda e: e[1], all_files)))
    with open(f'{path_to_dir_with_preprocessed_projects}/noneng_projects_stats.txt', 'w') as f:
        for k,v in sorted(stats.items()):
            f.write(f"{k} {v}\n")