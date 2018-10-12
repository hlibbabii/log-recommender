import argparse
import logging
import os
import pickle
import random
import re
from functools import partial
from multiprocessing.pool import Pool

from logrec.dataprep import parse_projects, path_to_non_eng_dicts, path_to_eng_dicts
from logrec.dataprep.lang.dao import DAO
from logrec.dataprep.lcsplitting.lowercase_words_splitter import load_english_dict
from logrec.dataprep.preprocessors.general import to_token_list
from logrec.dataprep.preprocessors.repr import DEFAULT_NO_COM_NO_STR, to_repr, DEFAULT, DEFAULT_NO_COM
from logrec.local_properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_PROJECT_LANGUAGE_CHECKER_ARGS


class LanguageChecker(object):
    DEFAULT_MIN_CHARS_TO_BE_NON_ENG = 4

    def __init__(self, path_to_general_english_dict, path_to_non_eng_dicts):
        logging.info("Loading english dictionary")
        english_general_dict = load_english_dict(path_to_general_english_dict)
        logging.info("Loading non-english dictionaries")
        self.non_eng_word_set = self.__create_non_eng_word_set(path_to_non_eng_dicts, english_general_dict,
                                                               LanguageChecker.DEFAULT_MIN_CHARS_TO_BE_NON_ENG)

    def in_non_eng_word_set(self, word):
        return word in self.non_eng_word_set

    def is_non_eng(self, word):
        return not self.__isascii(word) or self.in_non_eng_word_set(word.lower())

    def calc_lang_stats(self, word_list, include_sample=False):
        non_eng_unique=set()
        non_eng=0
        for word in word_list:
            if self.is_non_eng(word):
                non_eng+=1
                non_eng_unique.add(word)

        total = len(word_list)
        total_uq = len(set(word_list))
        non_eng_uq = len(non_eng_unique)
        result = total, total_uq, non_eng, non_eng_uq \
            ,float(non_eng) / total if total != 0 else 0 \
               ,float(non_eng_uq) /total_uq if total_uq != 0 else 0
        if include_sample:
            result = (*result, ",".join(random.sample(non_eng_unique, min(len(non_eng_unique), 15))))
        return result

    def __create_non_eng_word_set(self, dicts_dir, english_dict, min_chars):
        dict_files_names = [f for f in os.listdir(dicts_dir)]
        non_eng_words = set()
        for dict_file_name in dict_files_names:
            with open(os.path.join(dicts_dir, dict_file_name), 'r') as f:
                for line in f:
                    word = re.split("[/\t]", line)[0]  # splitting by tabs and slashes
                    word = word.lower()
                    if word[-1] == '\n':
                        word = word[:-1]
                    if word not in english_dict and len(word) >= min_chars:
                        non_eng_words.add(word)
        return non_eng_words

    def __isascii(self, str):
        try:
            str.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False


def get_project_name(file):
    pattern = f'(.*).{parse_projects.EXTENSION}'
    match = re.fullmatch(pattern, file)
    if match is not None:
        return match[1]
    else:
        raise AssertionError(f'File {file} does not match the pattern {pattern}')


def calc_stats(lang_checker, path_to_dir_with_preprocessed_projects, file):
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
                only_code_stats = lang_checker.calc_lang_stats(repr1)
                repr2 = to_token_list(to_repr(DEFAULT_NO_COM, token_list)).split()
                code_str_stats = lang_checker.calc_lang_stats(repr2)
                repr3 = to_token_list(to_repr(DEFAULT, token_list)).split()
                code_str_com_stats = lang_checker.calc_lang_stats(repr3, include_sample=True)

                filename = fn.readline()[:-1]
                file_stats.append((project_name, filename, *only_code_stats, *code_str_stats, *code_str_com_stats))
            except EOFError:
                break
    return file_stats if file_stats else [[project_name]]


def parsed_files_generator(path_to_dir_with_preprocessed_projects, dao):
    for file in os.listdir(path_to_dir_with_preprocessed_projects):
        if file.startswith(".") or get_project_name(file) in dao.processed_projects_cache:
            continue
        yield file


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-dataset-dir', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('preprocessed_dataset', help='path to preprocessed dataset relative '
                                                     'to the one passed as --base-dataset-dir param')

    args = parser.parse_args(*DEFAULT_PROJECT_LANGUAGE_CHECKER_ARGS)

    path_to_dir_with_preprocessed_projects = f'{args.base_dataset_dir}/{args.preprocessed_dataset}'

    logging.basicConfig(level=logging.DEBUG)
    if not os.path.exists(path_to_dir_with_preprocessed_projects):
        logging.error(f"Path: {path_to_dir_with_preprocessed_projects} does not exist")
        exit(1)

    language_checker = LanguageChecker(path_to_eng_dicts, path_to_non_eng_dicts)
    dao = DAO()
    ALWAYS_REWRITE = False

    if ALWAYS_REWRITE:
        logging.info("Purging db...")
        dao.purge()

    get_parsed_file_generator = lambda: parsed_files_generator(path_to_dir_with_preprocessed_projects, dao)
    total_projects = len([x for x in get_parsed_file_generator()])
    logging.info(f"Total projects to process: {total_projects}")
    counter = 0
    with Pool() as pool:
        results = pool.imap_unordered(partial(calc_stats, language_checker, path_to_dir_with_preprocessed_projects),
                                      get_parsed_file_generator())
        for result in results:
            project_name = result[0][0]
            logging.info(f'Processed {project_name}: ({counter} out of {total_projects})')
            counter += 1
            if len(result) > 1 or len(result[0]) > 1:
                for row in result:
                    try:
                        dao.save_row(row)
                    except Exception as ex:
                        print(ex)
            else:
                # project was empty
                logging.warning(f'No parsed files found in {project_name}')
            dao.save_processed_project(project_name)

    params = (0.006, 2.01, 2.01, 0.019, 3.939599999999999, 2.01)
    non_eng_projects = dao.select_noneng_projects(*params)
    noneng_projects_file = f'{args.base_dataset_dir}/noneng-projects.txt'
    logging.info(f"Writing non-english projects list to {noneng_projects_file}")
    with open(noneng_projects_file, 'w') as f:
        f.write(str(params) + '\n')
        for p in non_eng_projects:
            f.write(p + '\n')


if __name__ == '__main__':
    run()
