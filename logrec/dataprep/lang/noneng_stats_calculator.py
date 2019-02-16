import argparse
import logging
import os
import gzip
import pickle
import re
from functools import partial
from multiprocessing.pool import Pool

from logrec.dataprep import parse_projects, path_to_non_eng_dicts, path_to_eng_dicts, PARSED_DIR
from logrec.dataprep.lang.dao import DAO
from logrec.dataprep.lang.langchecker import LanguageChecker
from logrec.dataprep.preprocessors.general import to_token_list
from logrec.dataprep.prepconfig import PrepConfig
from logrec.dataprep.to_repr import to_repr
from logrec.dataprep.split.ngram import NgramSplitConfig
from logrec.infrastructure.fractions_manager import include_to_df

logger = logging.getLogger(__name__)


def get_project_name(file):
    pattern = f'(.*).{parse_projects.EXTENSION}'
    match = re.fullmatch(pattern, file)
    if match is not None:
        return match[1]
    else:
        raise AssertionError(f'File {file} does not match the pattern {pattern}')


def calc_stats_for_prepconfig(prepconfig, lang_checker, token_list, include_sample=False):
    repr = to_token_list(to_repr(PrepConfig.from_encoded_string(prepconfig), token_list, NgramSplitConfig())).split(' ')
    return lang_checker.calc_lang_stats(repr, include_sample=include_sample)


def calc_stats(lang_checker, path_to_dir_with_preprocessed_projects, train_test_valid, file):
    project_name = get_project_name(file)
    filenames_file = f'.{project_name}.{parse_projects.FILENAMES_EXTENSION}'
    file_stats = []
    with gzip.GzipFile(os.path.join(path_to_dir_with_preprocessed_projects, train_test_valid, file), 'rb') as f, \
            open(os.path.join(path_to_dir_with_preprocessed_projects, train_test_valid, filenames_file), 'r') as fn:
        _ = pickle.load(f)  # preprocessing param dict
        while True:
            try:
                token_list = pickle.load(f)

                only_code_stats = calc_stats_for_prepconfig('02110', lang_checker, token_list)
                code_str_stats = calc_stats_for_prepconfig('01110', lang_checker, token_list)
                code_str_com_stats = calc_stats_for_prepconfig('00110', lang_checker, token_list, include_sample=True)

                filename = fn.readline().rstrip('\n')
                file_stats.append(
                    (train_test_valid, project_name, filename, *only_code_stats, *code_str_stats, *code_str_com_stats))
            except EOFError:
                break
    return file_stats if file_stats else [[train_test_valid, project_name]]


def parsed_files_generator(path_to_dir_with_preprocessed_projects, train_test_valid, percent, start_from, dao):
    for file in os.listdir(os.path.join(path_to_dir_with_preprocessed_projects, train_test_valid)):
        if file.startswith(".") or get_project_name(file) in dao.processed_projects_cache:
            continue
        if include_to_df(file, percent, start_from):
            yield file


def run():
    from logrec.properties import DEFAULT_PARSED_DATASETS_DIR, DEFAULT_PROJECT_LANGUAGE_CHECKER_ARGS

    parser = argparse.ArgumentParser()
    parser.add_argument('--base-dataset-dir', default=DEFAULT_PARSED_DATASETS_DIR)
    parser.add_argument('dataset')
    parser.add_argument('train_test_valid')
    parser.add_argument('percent', type=float)
    parser.add_argument('start_from', type=float)

    args = parser.parse_args(*DEFAULT_PROJECT_LANGUAGE_CHECKER_ARGS)

    path_to_dir_with_preprocessed_projects = os.path.join(args.base_dataset_dir, args.dataset, PARSED_DIR)

    if not os.path.exists(path_to_dir_with_preprocessed_projects):
        logger.error(f"Path: {path_to_dir_with_preprocessed_projects} does not exist")
        exit(1)

    language_checker = LanguageChecker(path_to_eng_dicts, path_to_non_eng_dicts)
    dao = DAO()
    ALWAYS_REWRITE = False

    if ALWAYS_REWRITE:
        logger.info("Purging db...")
        dao.purge()

    get_parsed_file_generator = lambda: parsed_files_generator(path_to_dir_with_preprocessed_projects,
                                                               args.train_test_valid,
                                                               args.percent,
                                                               args.start_from,
                                                               dao)
    total_projects = len([x for x in get_parsed_file_generator()])
    logger.info(f"Total projects to process: {total_projects}")
    counter = 0
    with Pool() as pool:
        results = pool.imap_unordered(
            partial(calc_stats, language_checker, path_to_dir_with_preprocessed_projects, args.train_test_valid),
            get_parsed_file_generator())
        for result in results:
            train_test_valid = result[0][0]
            project_name = result[0][1]
            logger.info(f'Processed {train_test_valid}/{project_name}: ({counter} out of {total_projects})')
            counter += 1
            if len(result) > 1 or len(result[0]) > 2:
                for row in result:
                    try:
                        dao.save_row(row)
                    except Exception as ex:
                        print(ex)
            else:
                # project was empty
                logger.warning(f'No parsed files found in {train_test_valid}/{project_name}')
            dao.save_processed_project(project_name)

    params = (0.006, 2.01, 2.01, 0.019, 3.939599999999999, 2.01)
    non_eng_projects = dao.select_noneng_projects(*params)
    noneng_projects_file = os.path.join(args.base_dataset_dir, f'noneng-projects-{args.train_test_valid}.txt')
    logger.info(f"Writing non-english projects list to {noneng_projects_file}")
    with open(noneng_projects_file, 'w') as f:
        f.write(str(params) + '\n')
        for p in non_eng_projects:
            f.write(p + '\n')


if __name__ == '__main__':
    run()
