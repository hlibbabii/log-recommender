import os
from collections import defaultdict

from dataprep import base_project_dir
from dataprep.lcsplitting.lowercase_words_splitter import load_english_dict


def create_word_to_lang_map(dicts_dir, english_general_dict):
    dict_files_names = [f for f in os.listdir(dicts_dir)]
    word_to_lang_map = defaultdict(set)
    for dict_file_name in dict_files_names:
        with open(f'{path_to_dicts}/{dict_file_name}', 'r') as f:
            for line in f:
                word = line.split('/')[0]
                if word not in english_general_dict:
                    word_to_lang_map[word].add(dict_file_name.split(".")[0])
    word_to_lang_map.default_factory = None
    return word_to_lang_map


def calc_lang_stats(path_to_dir_with_preprocessed_projects, file, word_to_lang_map):
    lang_to_number = defaultdict(int)
    lang_to_word_examples = defaultdict(list)
    encountered_words = {}
    total = 0
    with open(os.path.join(path_to_dir_with_preprocessed_projects, file), 'r') as f:
        for line in f:
            for word in line.split():
                if word not in encountered_words:
                    total += 1
                    encountered_words[word] = 1
                    if word in word_to_lang_map:
                        langs_word_belongs_to = word_to_lang_map[word]
                        for lang in langs_word_belongs_to:
                            lang_to_number[lang] += 1
                            lang_to_word_examples[lang].append(word)

    lang_to_percent = {k: float(v) / total if total > 0 else 0 for k, v in lang_to_number.items()}
    return lang_to_percent, lang_to_word_examples, total, encountered_words


def check_more_than_limit(lang_to_percent):
    for v in lang_to_percent.values():
        if v > 0.01:
            return True
    return False


if __name__ == '__main__':
    path_to_dir_with_preprocessed_projects = f"{base_project_dir}/nn-data/devanbu_no_replaced_identifier_split_no_tabs/train"
    path_to_dicts = f"{base_project_dir}/dicts/"
    path_to_general_english_dict = f'{base_project_dir}/eng-dicts'

    english_general_dict = load_english_dict(path_to_general_english_dict)
    word_to_lang_map = create_word_to_lang_map(path_to_dicts, english_general_dict)

    for file in os.listdir(path_to_dir_with_preprocessed_projects):
        lang_to_percent, lang_to_word_examples, total, enc_words = \
            calc_lang_stats(path_to_dir_with_preprocessed_projects, file, word_to_lang_map)
        non_eng = check_more_than_limit(lang_to_percent)
        if non_eng:
            print(f'Gen stats: file:{file}, {lang_to_percent}, total: {total}')
            print(lang_to_word_examples)
