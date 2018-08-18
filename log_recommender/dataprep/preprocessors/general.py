import itertools
import re

###############   File lines level   ###########
from dataprep.preprocessors import java
from dataprep.preprocessors import placeholders
from dataprep.preprocessors.java import EOF
from dataprep.preprocessors.util import create_regex_from_token_list


def lines_to_one_lines_with_newlines(lines):
    return [w for line in lines for w in (line, EOF)]

###############   Multitoken list level   ###########


def replace_4whitespaces_with_tabs(multitokens):
    return list(map(lambda x: x.replace("    ", "\t"), multitokens))


def newline_and_tab_remover(tokens):
    return list(filter(lambda t: t != "\n" and t != "\t", tokens))


def to_string_repr(p):
    return repr(" ".join(p))[1:-1] + f" {placeholders['ect']}\n"


def spl(multitokens, two_char_delimiters, one_char_delimiter):
    two_char_regex = create_regex_from_token_list(two_char_delimiters)
    one_char_regex = create_regex_from_token_list(one_char_delimiter)
    return [w for spl in (map(lambda str: split_to_key_words_and_identifiers(str, two_char_regex, one_char_regex, java.delimiters_to_drop_verbose), multitokens))
            for w in spl]

def spl_verbose(multitokens):
    '''
    doesn't remove such tokens as tabs, newlines, brackets
    '''
    return spl(multitokens,
               java.two_character_tokens + java.two_char_verbose,
               java.one_character_tokens + java.one_char_verbose)


def split_to_key_words_and_identifiers(line, two_char_regex, one_char_regex, to_drop):
    two_char_tokens_separated = re.split(two_char_regex, line)
    result =[]
    for str in two_char_tokens_separated:
        if str in java.two_character_tokens:
            result.append(str)
        else:
            one_char_token_separated = re.split(one_char_regex, str)
            result.extend(list(filter(None, itertools.chain.from_iterable(
                [re.split(to_drop, str) for str in one_char_token_separated]
            ))))
    return result