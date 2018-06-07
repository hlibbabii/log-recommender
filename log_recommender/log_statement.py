import re
import itertools
import sys

from java_parser import JavaParser, two_character_tokens, one_character_tokens, delimiters_to_drop, \
    two_char_verbose, one_char_verbose, delimiters_to_drop_verbose, IDENTIFIER_SEPARATOR

__author__ = 'hlib'

class LogContext(object):
    def __init__(self, context_before, context_after):
        self.context_before = context_before
        self.context_after = context_after
        # self.context_words = preprocess_context(self.context_before + self.context_after)
        self.context_words = list(map(lambda x: preprocess_ctx(x, func_list=[
            replace_4whitespaces_with_tabs,
            spl,
            lambda context_line: [item.lower() for identifier in context_line for item in camel_case_split(identifier)]
        ]), self.context_before))

    def get_context_words(self, n_lines_to_consider):
        return [w for w_list in self.context_words[-n_lines_to_consider:] for w in w_list]

    def get_marked_up_context(self, interesting_words):
        BEFORE = "[red]##"
        AFTER = "##"
        locations=[]
        concat_context_before = "".join(self.context_before)
        lowercase_context = concat_context_before.lower()
        start_position = 0
        continue_search_from_index = 0
        symbols_at_least_skipped = 0
        merged_context_words = self.get_context_words(sys.maxsize)
        for word in interesting_words:
            if word == '':
                raise AssertionError("word is empty in " + interesting_words)
            next_word_list_index = continue_search_from_index + merged_context_words[continue_search_from_index:].index(word)
            symbols_at_least_skipped = start_position + \
                        sum(map(lambda x: len(x), merged_context_words[continue_search_from_index:next_word_list_index]))
            continue_search_from_index = next_word_list_index + 1
            found_start = lowercase_context.find(word, max(start_position, symbols_at_least_skipped))
            if found_start == -1 or next_word_list_index == -1:
                raise AssertionError(word + " not found in:\n" + concat_context_before + "")
            locations.append((concat_context_before[start_position:found_start],
                             concat_context_before[found_start: found_start + len(word)]))
            start_position = found_start + len(word)
        last_location = concat_context_before[start_position:]
        marked_up_string = "[literal,subs=\"quotes\"]\n"
        for location in locations:
            # marked_up_string += RAW
            marked_up_string += location[0]
            # marked_up_string += RAW
            marked_up_string += BEFORE
            # marked_up_string += RAW
            marked_up_string += location[1]
            # marked_up_string += RAW
            marked_up_string += AFTER
        marked_up_string += last_location
        return marked_up_string


log_count = 0


def preprocess_ctx(context, func_list):
    pp_context = context
    for func in func_list:
        pp_context = func(pp_context)
    return pp_context


class LogStatement(object):

    log_count = 0

    def __init__(self, text_line, text, text_words, level, n_variables,
                 context_before, context_after, project, link):
        self.text_line = text_line
        self.text = text
        self.text_words = text_words
        self.level = level
        self.n_variables = n_variables
        self.context = LogContext(context_before, context_after)
        self.project = project
        self.link = link
        self.id = self.__generate_id__()

    def neg_or_pos(self):
        return 'pos' if self.level in ['trace', 'debug', 'info'] else 'neg'

    def __generate_id__(self):
        id = self.project[:6] + "_" + str(LogStatement.log_count)
        LogStatement.log_count += 1
        return id

    def get_first_words(self, how_many):
        first_words = self.text_words[:how_many]
        first_words.extend([''] * (how_many - len(first_words)))
        return first_words


    def get_first_word(self):
        return self.text_words[0] if len(self.text_words) > 0 else ""

    def get_marked_up_context(self, interesting_words):
        return self.context.get_marked_up_context(interesting_words)

    def get_context_words(self, n_lines_to_consider):
        return self.context.get_context_words(n_lines_to_consider)


def create_regex_from_token_list(token_list):
    m = list(map(lambda x:
             x.replace('\\', '\\\\')
                 .replace("+", "\+")
                 .replace("|", "\|")
                 .replace("*", "\*")
                 .replace("[", "\[")
                 .replace("]", "\]")
                 .replace("-", "\-")
                 .replace('"', '\\"')
                 .replace('?', "\?")
                 .replace('(', "\(")
                 .replace(')', "\)")
                 .replace(".", "\.")


                 , token_list))
    return "(" + "|".join(
        m
    ) +")"

def add_between_elements(list, what_to_add):
    return [w for part in list for w in (part, what_to_add)][:-1]

def camel_case_split(identifier, add_separator=False):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    parts = [m.group(0) for m in matches]
    return add_between_elements(parts, IDENTIFIER_SEPARATOR) if add_separator else parts

def underscore_split(identifier, add_separator=False):
    #TODO it creates empty element if the identifier starts or ends with underscore
    parts = identifier.split("_")
    return add_between_elements(parts, IDENTIFIER_SEPARATOR) if add_separator else parts

def replace_4whitespaces_with_tabs(s):
    return s.replace("    ", "\t")

def merge_tabs(lst):
    res = []
    count = 0
    for word in lst:
        if word == '\t':
            count += 1
        else:
            if count != 0:
                res.append('\t' + str(count))
                count = 0
            res.append(word)
    if count != 0:
        res.append('\t' + str(count))
    return res

def spl(line):
    two_char_regex = create_regex_from_token_list(two_character_tokens)
    one_char_regex = create_regex_from_token_list(one_character_tokens)
    return split_to_key_words_and_identifiers(line, two_char_regex, one_char_regex, delimiters_to_drop)

def spl_verbose(line):
    two_char_regex = create_regex_from_token_list(two_character_tokens + two_char_verbose)
    one_char_regex = create_regex_from_token_list(one_character_tokens + one_char_verbose)
    return split_to_key_words_and_identifiers(line, two_char_regex, one_char_regex, delimiters_to_drop_verbose)

def split_to_key_words_and_identifiers(line, two_char_regex, one_char_regex, to_drop):
    two_char_tokens_separated = re.split(two_char_regex, line)
    result =[]
    for str in two_char_tokens_separated:
        if str in two_character_tokens:
            result.append(str)
        else:
            one_char_token_separated = re.split(one_char_regex, str)
            result.extend(list(filter(None, itertools.chain.from_iterable(
                [re.split(to_drop, str) for str in one_char_token_separated]
            ))))
    return result


def filter_out_1_and_2_char_tokens(context):
    return list(filter(lambda x: x not in one_character_tokens and x not in two_character_tokens, context))