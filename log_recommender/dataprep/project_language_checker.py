import argparse
import csv
import logging
import math
import os
import pickle
import re
import shutil
from collections import defaultdict
from multiprocessing.pool import Pool

import psycopg2

from dataprep import base_project_dir, parse_projects
from dataprep.lcsplitting.lowercase_words_splitter import load_english_dict
from dataprep.preprocessors.general import to_token_list
from dataprep.preprocessors.noneng import isascii
from dataprep.preprocessors.repr import DEFAULT_NO_COM_NO_STR, to_repr, DEFAULT, DEFAULT_NO_COM
from local_properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_PROJECT_LANGUAGE_CHECKER_ARGS

DEFAULT_MIN_FREQ_TO_BE_NON_ENG = 0.01
DEFAULT_MIN_WORDS_TO_BE_NON_ENG = 5
DEFAULT_MIN_CHARS_TO_BE_NON_ENG=4


def create_non_eng_word_set(dicts_dir, english_general_dict, min_chars):
    dict_files_names = [f for f in os.listdir(dicts_dir)]
    non_eng_words=set()
    for dict_file_name in dict_files_names:
        with open(os.path.join(dicts_dir,dict_file_name), 'r') as f:
            for line in f:
                word = line.split('/')[0]
                if word not in english_general_dict and len(word) >= min_chars:
                    non_eng_words.add(word)
    return non_eng_words

class LanguageChecker(object):
    def __init__(self):
        logging.info("Loading english dictionary")
        english_general_dict = load_english_dict(path_to_general_english_dict)
        logging.info("Loading non-english dictionaries")
        self.non_eng_word_set = create_non_eng_word_set(path_to_non_eng_dicts, english_general_dict, min_chars_to_be_non_eng)

    def in_non_eng_word_set(self, word):
        return word in self.non_eng_word_set

    def is_non_eng(self, word):
        return not isascii(word) or self.in_non_eng_word_set(word)


    def calc_lang_stats(self, word_list):
        non_eng_unique=set()
        non_eng=0
        for word in word_list:
            if self.is_non_eng(word):
                non_eng+=1
                non_eng_unique.add(word)

        total = len(word_list)
        total_uq = len(set(word_list))
        non_eng_uq = len(non_eng_unique)
        return total, total_uq, non_eng, non_eng_uq \
               ,float(non_eng) / total if total != 0 else 0 \
               ,float(non_eng_uq) /total_uq if total_uq != 0 else 0


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


def write_to_csv(file_stats):
    with open(f'{base_project_dir}/generated_stats/langs.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(
            ['Project', 'File', 'code total', 'code total uq', 'code noneng', 'code noneng uq', '%', '%(uq)',
             'code + str total', 'code + str total uq', 'code + str noneng', 'code + str noneng uq', '%', '%(uq)',
             'code + str + com total', 'code + str + com total uq', 'code + str + com noneng',
             'code + str + com noneng uq', '%', '%(uq)'
             ])
        for row in file_stats:
            writer.writerow(row)


def get_project_name(file):
    pattern = f'(.*).{parse_projects.EXTENSION}'
    match = re.fullmatch(pattern, file)
    if match is not None:
        return match[1]
    else:
        raise AssertionError(f'File {file} does not match the pattern {pattern}')


def calc_stats(file):
    project_name = get_project_name(file)
    filenames_file = f'.{project_name}.{parse_projects.FILENAMES_EXTENSION}'
    file_stats = []
    with open(os.path.join(path_to_dir_with_preprocessed_projects, file), 'rb') as f, \
            open(os.path.join(path_to_dir_with_preprocessed_projects, filenames_file), 'r') as fn:
        _ = pickle.load(f)  # preprocessing param dict
        while True:
            try:
                token_list = pickle.load(f)

                repr1 = to_token_list(to_repr(DEFAULT_NO_COM_NO_STR, token_list)).split()
                only_code_stats = language_checker.calc_lang_stats(repr1)
                repr2 = to_token_list(to_repr(DEFAULT_NO_COM, token_list)).split()
                code_str_stats = language_checker.calc_lang_stats(repr2)
                repr3 = to_token_list(to_repr(DEFAULT, token_list)).split()
                code_str_com_stats = language_checker.calc_lang_stats(repr3)

                filename = fn.readline()[:-1]
                file_stats.append((project_name, filename, *only_code_stats, *code_str_stats, *code_str_com_stats))
            except EOFError:
                break
    return file_stats

def parsed_files_generator(path_to_dir_with_preprocessed_projects, persistent_chunk_tracker):
    for file in os.listdir(path_to_dir_with_preprocessed_projects):
        if file.startswith(".") or persistent_chunk_tracker.is_tracked(get_project_name(file)):
            continue
        yield file


class PersistentChunkTracker(object):
    def __init__(self):
        self.dir = f'{base_project_dir}/generated_stats/~langs/'

    def track(self, project_name):
        open(f'{self.dir}/{project_name}', 'a').close()

    def is_tracked(self, project_name):
        return os.path.exists(f'{self.dir}/{project_name}')

    def untrack_all(self):
        if os.path.exists(self.dir):
            shutil.rmtree(self.dir)

    def is_tracking(self):
        return os.path.exists(self.dir)

    def start_tracking(self):
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)


class DAO(object):
    def __init__(self):
        conn = psycopg2.connect("dbname='logrec' "
                                "user='logrec' "
                                "host='logrec.cpdobqsbhnep.eu-central-1.rds.amazonaws.com' "
                                "password='logrec'")
        conn.set_session(autocommit=True)
        self.cur = conn.cursor()

    def save_row(self, row):
        execute = self.cur.execute('INSERT INTO LANGSTATS (PROJECT, FILE, ' \
                                   ' CODE_TOTAL, CODE_TOTAL_UQ, CODE_NON_ENG, CODE_NON_ENG_UQ, CODE_PERCENT, CODE_PERCENT_UQ,' \
                                   ' CODE_STR_TOTAL, CODE_STR_TOTAL_UQ, CODE_STR_NON_ENG, CODE_STR_NON_ENG_UQ, CODE_STR_PERCENT, CODE_STR_PERCENT_UQ,' \
                                   ' CODE_STR_COM_TOTAL, CODE_STR_COM_TOTAL_UQ, CODE_STR_COM_NON_ENG, CODE_STR_COM_NON_ENG_UQ, CODE_STR_COM_PERCENT, CODE_STR_COM_PERCENT_UQ) ' \
                                   'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                                   row)

    def delete_all_rows(self):
        self.cur.execute("DELETE FROM LANGSTATS")

    def rows_present(self):
        return self.cur.execute("SELECT * FROM LANGSTATS")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-freq', type=float, default=f'{DEFAULT_MIN_FREQ_TO_BE_NON_ENG}')
    parser.add_argument('--min-words', type=int, default=f'{DEFAULT_MIN_WORDS_TO_BE_NON_ENG}')
    parser.add_argument('--min-chars', type=int, default=f'{DEFAULT_MIN_CHARS_TO_BE_NON_ENG}')
    parser.add_argument('--base-dataset-dir', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('preprocessed_dataset', help='path to preprocessed dataset relative '
                                                     'to the one passed as --base-dataset-dir param')

    args = parser.parse_args(*DEFAULT_PROJECT_LANGUAGE_CHECKER_ARGS)

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


    language_checker = LanguageChecker()
    persistent_chunk_tracker = PersistentChunkTracker()
    dao = DAO()
    ALWAYS_REWRITE=True

    if ALWAYS_REWRITE:
        persistent_chunk_tracker.untrack_all()
        dao.delete_all_rows()
    elif not persistent_chunk_tracker.is_tracking() and dao.rows_present():
        logging.info(f"Stats has already been generated!")
        exit(0)
    persistent_chunk_tracker.start_tracking()

    get_parsed_file_generator = lambda: parsed_files_generator(path_to_dir_with_preprocessed_projects, persistent_chunk_tracker)
    total_projects = len([x for x in get_parsed_file_generator()])
    logging.info(f"Total projects to process: {total_projects}")
    with Pool() as pool:
        results = pool.imap_unordered(calc_stats, get_parsed_file_generator())
        for result in results:
            for row in result:
                dao.save_row(row)
            project_name = result[0][0]
            persistent_chunk_tracker.track(project_name)
    persistent_chunk_tracker.untrack_all()

