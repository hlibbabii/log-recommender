import itertools
import re
import sys
from functools import partial

from java_parser import two_character_tokens, one_character_tokens, one_char_verbose, two_char_verbose, \
    delimiters_to_drop, delimiters_to_drop_verbose, IDENTIFIER_SEPARATOR, JavaParser, EOF


#=====  UTIL ====================

def add_between_elements(list, what_to_add):
    return [w for part in list for w in (part, what_to_add)][:-1]

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

#=====  Token level  ============

def camel_case_split(identifier, add_separator=False):
    if identifier == '\n': #TODO XXX
        return [identifier]
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    parts = [m.group(0) for m in matches]
    return add_between_elements(parts, IDENTIFIER_SEPARATOR) if add_separator else parts


def underscore_split(identifier, add_separator=False):
    #TODO it creates empty element if the identifier starts or ends with underscore
    parts = identifier.split("_")
    return add_between_elements(parts, IDENTIFIER_SEPARATOR) if add_separator else parts

#======== Token list level   ==========

def merge_tabs(tokens):
    res = []
    count = 0
    for word in tokens:
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

#======== Multitoken list level   ==========

def replace_4whitespaces_with_tabs(multitokens):
    return list(map(lambda x: x.replace("    ", "\t"), multitokens))

def spl(multitokens, two_char_delimiters, one_char_delimiter):
    two_char_regex = create_regex_from_token_list(two_char_delimiters)
    one_char_regex = create_regex_from_token_list(one_char_delimiter)
    return [w for spl in (map(lambda str: split_to_key_words_and_identifiers(str, two_char_regex, one_char_regex, delimiters_to_drop_verbose), multitokens))
            for w in spl]


def spl_non_verbose(line):
    return spl(line, two_character_tokens, one_character_tokens)


def spl_verbose(line):
    '''
    doesn't remove such tokens as tabs, newlines, brackets
    '''
    return spl(line,
               two_character_tokens + two_char_verbose,
               one_character_tokens + one_char_verbose)


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


def filter_out_1_and_2_char_tokens(tokens):
    return list(filter(lambda x: x not in one_character_tokens and x not in two_character_tokens, tokens))


split_line_canel_case = lambda context_line: [item.lower() for identifier in context_line for item in camel_case_split(identifier, add_separator=True)]
split_line_underscore = lambda context_line: [item for identifier in context_line for item in underscore_split(identifier, add_separator=True)]


def name_to_func(name, interesting_context_words):
    java_parser = JavaParser()
    if name == 'java.strip_off_identifiers':
        return partial(java_parser.strip_off_identifiers, interesting_context_words)
    elif name.startswith("java."):
        return partial(getattr(JavaParser, name[5:]), java_parser)
    else:
        return getattr(sys.modules[__name__], name)


def newline_and_tab_remover(tokens):
    return list(filter(lambda t: t != "\n" and t != "\t", tokens))


def preprocess_ctx(context, func_list):
    pp_context = context
    for func in func_list:
        pp_context = func(pp_context)
    return pp_context


def process_full_identifiers(context, preprocessors, interesting_context_words):
    string_list = [w for line in context for w in (line, EOF)]
    processed = preprocess_ctx(string_list, list(map(lambda p: name_to_func(p, interesting_context_words), preprocessors)))
    processed = repr(" ".join(processed))[1:-1] + " <ect>\n"
    return processed