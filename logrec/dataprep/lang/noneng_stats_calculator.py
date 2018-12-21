import argparse
import logging
import os
import pickle
import re
from functools import partial
from multiprocessing.pool import Pool

from logrec.dataprep import parse_projects, path_to_non_eng_dicts, path_to_eng_dicts
from logrec.dataprep.lang.dao import DAO
from logrec.dataprep.lang.langchecker import LanguageChecker
from logrec.dataprep.preprocessors.general import to_token_list
from logrec.dataprep.preprocessors.preprocessing_types import PreprocessingParam
from logrec.dataprep.to_repr import to_repr

logger = logging.getLogger(__name__)

DEFAULT_NO_COM_NO_STR = {
    PreprocessingParam.NO_COM_STR: 2,
    PreprocessingParam.SPL: 2,
    PreprocessingParam.NO_SEP: 0,
    PreprocessingParam.NO_NEWLINES_TABS: 1,
    PreprocessingParam.NO_LOGS: 0,
}

DEFAULT_NO_COM = {
    PreprocessingParam.NO_COM_STR: 1,
    PreprocessingParam.SPL: 2,
    PreprocessingParam.NO_SEP: 0,
    PreprocessingParam.NO_NEWLINES_TABS: 1,
    PreprocessingParam.NO_LOGS: 0,
}

DEFAULT = {
    PreprocessingParam.NO_COM_STR: 0,
    PreprocessingParam.SPL: 2,
    PreprocessingParam.NO_SEP: 0,
    PreprocessingParam.NO_NEWLINES_TABS: 1,
    PreprocessingParam.NO_LOGS: 0
}


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
    from logrec.local_properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_PROJECT_LANGUAGE_CHECKER_ARGS

    parser = argparse.ArgumentParser()
    parser.add_argument('--base-dataset-dir', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('preprocessed_dataset', help='path to preprocessed dataset relative '
                                                     'to the one passed as --base-dataset-dir param')

    args = parser.parse_args(*DEFAULT_PROJECT_LANGUAGE_CHECKER_ARGS)

    path_to_dir_with_preprocessed_projects = os.path.join(args.base_dataset_dir, args.preprocessed_dataset)

    logging.basicConfig(level=logging.DEBUG)
    if not os.path.exists(path_to_dir_with_preprocessed_projects):
        logger.error(f"Path: {path_to_dir_with_preprocessed_projects} does not exist")
        exit(1)

    language_checker = LanguageChecker(path_to_eng_dicts, path_to_non_eng_dicts)
    dao = DAO()
    ALWAYS_REWRITE = False

    if ALWAYS_REWRITE:
        logger.info("Purging db...")
        dao.purge()

    get_parsed_file_generator = lambda: parsed_files_generator(path_to_dir_with_preprocessed_projects, dao)
    total_projects = len([x for x in get_parsed_file_generator()])
    logger.info(f"Total projects to process: {total_projects}")
    counter = 0
    with Pool() as pool:
        results = pool.imap_unordered(partial(calc_stats, language_checker, path_to_dir_with_preprocessed_projects),
                                      get_parsed_file_generator())
        for result in results:
            project_name = result[0][0]
            logger.info(f'Processed {project_name}: ({counter} out of {total_projects})')
            counter += 1
            if len(result) > 1 or len(result[0]) > 1:
                for row in result:
                    try:
                        dao.save_row(row)
                    except Exception as ex:
                        print(ex)
            else:
                # project was empty
                logger.warning(f'No parsed files found in {project_name}')
            dao.save_processed_project(project_name)

    params = (0.006, 2.01, 2.01, 0.019, 3.939599999999999, 2.01)
    non_eng_projects = dao.select_noneng_projects(*params)
    noneng_projects_file = os.path.join(args.base_dataset_dir, 'noneng-projects.txt')
    logger.info(f"Writing non-english projects list to {noneng_projects_file}")
    with open(noneng_projects_file, 'w') as f:
        f.write(str(params) + '\n')
        for p in non_eng_projects:
            f.write(p + '\n')


if __name__ == '__main__':
    run()
