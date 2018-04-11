import re
import itertools

__author__ = 'hlib'


class LogStatement(object):
    def __init__(self, log_text_line, log_text, log_text_words, log_level, n_variables,
                 context_before, context_after, project, link):
        self.log_text_line = log_text_line
        self.log_text = log_text
        self.log_text_words = log_text_words
        self.log_level = log_level
        self.n_variables = n_variables
        self.context_before = context_before
        self.context_after = context_after
        self.context_words = preprocess_context(self.context_before + self.context_after)
        self.project = project
        self.link = link

    def get_first_word(self):
        return self.log_text_words[0] if len(self.log_text_words) > 0 else ""

two_character_tokens = [
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

def two_character_tokens_regex():
    m = list(map(lambda x: x.replace("+", "\+").replace("|", "\|").replace("*", "\*"), two_character_tokens))
    return "(" + "|".join(
        m
    ) +")"

one_character_tokens = "(=|\+|\*|!|/|>|<)"

delimiters_to_drop = "[\[\] ,.\-?:\n\t(){};\"&|_#\\\@$]"


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]

def split_to_key_words_and_identifiers(line):
    regex = two_character_tokens_regex()
    two_char_tokens_separated = re.split(regex, line)
    result =[]
    for str in two_char_tokens_separated:
        if str in two_character_tokens:
            result.append(str)
        else:
            one_char_token_separated = re.split(one_character_tokens, str)
            result.extend(list(filter(None, itertools.chain.from_iterable(
                [re.split(delimiters_to_drop, str) for str in one_char_token_separated]
            ))))
    return result

def preprocess_context(context):
    context = split_to_key_words_and_identifiers(context)
    context = [item.lower() for identifier in context for item in camel_case_split(identifier)]
    return context