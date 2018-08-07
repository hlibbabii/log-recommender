from collections import defaultdict

from tqdm import tqdm

from dataprep import base_project_dir
from dataprep.lcsplitting.lowercase_words_splitter import load_english_dict


def get_possible_fixes_candidates(word):
    ln = len(word)
    return len_to_words_in_dict[ln - 1] + len_to_words_in_dict[ln] + len_to_words_in_dict[ln + 1]


from Levenshtein.StringMatcher import StringMatcher


def fl(word, word_from_dict):
    if len(word) != len(word_from_dict):
        return False
    for i in range(len(word) - 1):
        if (word[:i] + word[i + 1] + word[i] + word[i + 2:]) == word_from_dict:
            return True
    return False


def is_typo(word, word_from_dict):
    sm = StringMatcher()
    sm.set_seq1(word)
    sm.set_seq2(word_from_dict)
    dist = sm.distance()
    return dist == 1 or (dist == 2 and fl(word, word_from_dict))


if __name__ == '__main__':
    path_to_typo_candidates = f"{base_project_dir}/nn-data/devanbu_no_replaced_identifier_split_no_tabs_new_splits3_under_5000_15_percent/splits/0/typos.txt"
    file_with_fixes = f"{base_project_dir}/nn-data/devanbu_no_replaced_identifier_split_no_tabs_new_splits3_under_5000_15_percent/splits/0/fixes.txt"

    words_with_typos = []
    with open(path_to_typo_candidates, 'r') as f:
        for line in f:
            words_with_typos.append(line[:-1])

    general_dict = load_english_dict(f'{base_project_dir}/eng-dicts')
    len_to_words_in_dict = defaultdict(list)
    for w in general_dict:
        len_to_words_in_dict[len(w)].append(w)
    len_to_words_in_dict.default_factory = None


    with open(file_with_fixes, 'w') as f:
        for word in tqdm(words_with_typos):
            possible_fixes = []
            for word_from_dict in get_possible_fixes_candidates(word):
                if is_typo(word, word_from_dict):
                    possible_fixes.append(word_from_dict)
            stringified_possible_fixes = " ".join(possible_fixes)
            f.write(f"{word}|{stringified_possible_fixes}\n")
