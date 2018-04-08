import re

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


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]

def split_to_key_words_and_identifiers(line):
    return list(filter(None, re.split("[\[\] ,.\-!?:\n\t(){};=+*/\"&|<>_#\\\@$]+", line)))

def preprocess_context(context):
    context = split_to_key_words_and_identifiers(context)
    context = [item.lower() for identifier in context for item in camel_case_split(identifier)]
    return context