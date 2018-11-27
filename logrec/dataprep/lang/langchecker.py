import logging
import os
import random
import re

from logrec.dataprep.split.samecase.splitter import load_english_dict

logger = logging.getLogger(__name__)


class LanguageChecker(object):
    DEFAULT_MIN_CHARS_TO_BE_NON_ENG = 4

    def __init__(self, path_to_general_english_dict, path_to_non_eng_dicts):
        logger.info("Loading english dictionary")
        english_general_dict = load_english_dict(path_to_general_english_dict)
        logger.info("Loading non-english dictionaries")
        self.non_eng_word_set = self.__create_non_eng_word_set(path_to_non_eng_dicts, english_general_dict,
                                                               LanguageChecker.DEFAULT_MIN_CHARS_TO_BE_NON_ENG)

    def in_non_eng_word_set(self, word):
        return word in self.non_eng_word_set

    def is_non_eng(self, word):
        return not self.__isascii(word) or self.in_non_eng_word_set(word.lower())

    def calc_lang_stats(self, word_list, include_sample=False):
        non_eng_unique = set()
        non_eng = 0
        for word in word_list:
            if self.is_non_eng(word):
                non_eng += 1
                non_eng_unique.add(word)

        total = len(word_list)
        total_uq = len(set(word_list))
        non_eng_uq = len(non_eng_unique)
        result = total, total_uq, non_eng, non_eng_uq \
            , float(non_eng) / total if total != 0 else 0 \
            , float(non_eng_uq) / total_uq if total_uq != 0 else 0
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
