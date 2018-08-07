import os
from collections import defaultdict

from dataprep.lcsplitting.lowercase_words_splitter import load_english_dict

path_to_preprocessed_project_file = "/home/hlib/thesis/log-recommender/nn-data/devanbu_no_replaced_identifier_split_no_tabs/train/context.1.src"

path_to_dicts = "/home/hlib/thesis/log-recommender/dicts/"

lang_to_number = defaultdict(int)
lang_to_word_examples = defaultdict(list)

english_general_dict = load_english_dict(f'/usr/share/dict/words')

dict_files_names = [f for f in os.listdir("/home/hlib/thesis/log-recommender/dicts")]
word_to_lang_map = {}
for dict_file_name in dict_files_names:
    with open(f'{path_to_dicts}/{dict_file_name}', 'r') as f:
        for line in f:
            word = line.split('/')[0]
            if word not in english_general_dict:
                word_to_lang_map[word] = dict_file_name.split(".")[0]

# print(word_to_lang_map)

total = 0
with open(path_to_preprocessed_project_file, 'r') as f:
    for line in f:
        for word in line.split():
            total += 1
            if word in word_to_lang_map:
                if word not in lang_to_word_examples[word_to_lang_map[word]]:
                    lang_to_number[word_to_lang_map[word]] += 1
                    lang_to_word_examples[word_to_lang_map[word]].append(word)

lang_to_percent = {k: float(v) / total for k, v in lang_to_number.items()}
print(lang_to_percent)
print(lang_to_word_examples)
