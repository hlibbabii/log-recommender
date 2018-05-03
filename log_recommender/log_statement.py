import re
import itertools

__author__ = 'hlib'


class LogStatement(object):
    def __init__(self, text_line, text, text_words, level, n_variables,
                 context_before, context_after, project, link):
        self.text_line = text_line
        self.text = text
        self.text_words = text_words
        self.level = level
        self.n_variables = n_variables
        self.context_before = context_before
        self.context_after = context_after
        # self.context_words = preprocess_context(self.context_before + self.context_after)
        self.context_words = preprocess_context(self.context_before)
        self.project = project
        self.link = link

    def get_first_word(self):
        return self.text_words[0] if len(self.text_words) > 0 else ""

two_character_tokens = [
    "/*",
    "*/",
    "==",
    "!=",
    "**",
    "//",
    "++",
    "--",
    "+=",
    "-=",
    "/=",
    "*=",
    "%="
    "<=",
    ">=",
    "&&",
    "||"
]

one_character_tokens = [
    "+",
    "*",
    "!",
    "/",
    ">",
    "<",
    "="
]

def create_regex_from_token_list(token_list):
    m = list(map(lambda x: x.replace("+", "\+").replace("|", "\|").replace("*", "\*"), token_list))
    return "(" + "|".join(
        m
    ) +")"


delimiters_to_drop = "[\[\] ,.\-?:\n\t(){};\"&|_#\\\@$]"


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]

def split_to_key_words_and_identifiers(line):
    regex = create_regex_from_token_list(two_character_tokens)
    two_char_tokens_separated = re.split(regex, line)
    result =[]
    for str in two_char_tokens_separated:
        if str in two_character_tokens:
            result.append(str)
        else:
            one_char_token_separated = re.split(create_regex_from_token_list(one_character_tokens), str)
            result.extend(list(filter(None, itertools.chain.from_iterable(
                [re.split(delimiters_to_drop, str) for str in one_char_token_separated]
            ))))
    return result

FILTER_OUT_1_AND_2_CHAR_TOKENS = False


def filter_out_1_and_2_char_tokens(context):
    return list(filter(lambda x: x not in one_character_tokens and x not in two_character_tokens, context))


def preprocess_context(context):
    context = split_to_key_words_and_identifiers(context)
    if FILTER_OUT_1_AND_2_CHAR_TOKENS:
        context = filter_out_1_and_2_char_tokens(context)
    context = [item.lower() for identifier in context for item in camel_case_split(identifier)]
    return context