import itertools
import re

###############   File lines level   ###########
from dataprep.preprocessors import java
from dataprep.preprocessors.model.chars import NewLine, MultilineCommentEnd, MultilineCommentStart, OneLineCommentStart, \
    Quote, Backslash, Tab
from dataprep.preprocessors.model.general import ProcessableToken, ProcessableTokenContainer
from dataprep.preprocessors.model.placeholders import placeholders
from dataprep.preprocessors.util import create_regex_from_token_list


def lines_to_one_lines_with_newlines(lines, context):
    return [w for line in lines for w in (ProcessableToken(line if len(line) > 0 and line[-1] != '\n' else line[:-1]), NewLine())]

###############   Multitoken list level   ###########


def replace_4whitespaces_with_tabs(token_list, context):
    result = []
    for token in token_list:
        if isinstance(token, ProcessableToken):
            split_line = re.split("( {4})", token.get_val())
            result.extend([(Tab() if w == " "*4 else ProcessableToken(w)) for w in split_line])
        elif isinstance(token, ProcessableTokenContainer):
            for subtoken in token.get_subtokens():
                result.extend(replace_4whitespaces_with_tabs(subtoken))
        else:
            result.append(token)
    return result


def to_token_list(tokens):
    return repr(" ".join(map(lambda t : str(t),tokens)))[1:-1] + f" {placeholders['ect']}\n"

def to_human_readable(tokens, context):
    return " ".join(map(lambda t : str(t),tokens)) + "\n"


def spl(token_list, two_char_delimiters, one_char_delimiter):
    two_char_regex = create_regex_from_token_list(two_char_delimiters)
    one_char_regex = create_regex_from_token_list(one_char_delimiter)
    split_nested_list = list(map(
        lambda token: split_to_key_words_and_identifiers(token, two_char_regex, one_char_regex,
                                                         java.delimiters_to_drop_verbose), token_list))
    return [w for lst in split_nested_list for w in lst]

def spl_verbose(token_list, context):
    '''
    doesn't remove such tokens as tabs, newlines, brackets
    '''
    return spl(token_list,
               java.two_character_tokens + java.two_char_verbose,
               java.one_character_tokens + java.one_char_verbose)

characters = set(java.two_character_tokens + java.two_char_verbose + java.one_character_tokens + java.one_char_verbose)

def split_to_key_words_and_identifiers(token, two_char_regex, one_char_regex, to_drop):
    if isinstance(token, ProcessableToken):
        raw_result = []
        result = []
        two_char_tokens_separated = re.split(two_char_regex, token.get_val())
        for str in two_char_tokens_separated:
            if str in java.two_character_tokens:
                raw_result.append(str)
            else:
                one_char_token_separated = re.split(one_char_regex, str)
                raw_result.extend(list(filter(None, itertools.chain.from_iterable(
                    [re.split(to_drop, str) for str in one_char_token_separated]
                ))))
        for raw_str in raw_result:
            if not raw_str in characters:
                result.append(ProcessableToken(raw_str))
            elif raw_str == "/*":
                result.append(MultilineCommentStart())
            elif raw_str == "*/":
                result.append(MultilineCommentEnd())
            elif raw_str == "//":
                result.append(OneLineCommentStart())
            elif raw_str == "\"":
                result.append(Quote())
            elif raw_str == "\\":
                result.append(Backslash())
            elif raw_str == "\t":
                result.append(Tab())
            else:
                result.append(raw_str)
        return result
    elif isinstance(token, ProcessableTokenContainer):
        res = []
        for subtoken in token.get_subtokens():
            res.extend(split_to_key_words_and_identifiers(subtoken, two_char_regex, one_char_regex, to_drop))
        return res
    else:
        return [token]