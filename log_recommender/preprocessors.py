import itertools
import logging
import re
import sys
import time
from functools import partial
from java_parser import NUMBER_REGEX

logging.basicConfig(level=logging.DEBUG)

from java_parser import two_character_tokens, one_character_tokens, one_char_verbose, two_char_verbose, \
    delimiters_to_drop, delimiters_to_drop_verbose, JavaParser, EOF, placeholders

VAR_PLACEHOLDER = "<VAR>"
STRING_RESOURCE_PLACEHOLDER = "<STRING_RESOURCE>"

#=====  UTIL ====================

def add_between_elements(list, what_to_add):
    return [w for part in list for w in (part, what_to_add)][:-1]

def create_regex_from_token_list(token_list):
    m = list(map(lambda x:
             x.replace('\\', '\\\\')
                 .replace("^", "\\^")
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

#=====  Multitoken level =====================

def remove_placeholders(multitoken):
    multitoken = re.sub(VAR_PLACEHOLDER, r'', multitoken)
    multitoken = re.sub(STRING_RESOURCE_PLACEHOLDER, r'', multitoken)
    return multitoken


def strip_line(multitoken):
    return multitoken.strip()


def replace_string_resources_names(multitoken):
    changed = re.sub('^([0-9a-zA-Z]+\\.)+[0-9a-zA-Z]+$', STRING_RESOURCE_PLACEHOLDER, multitoken)
    changed = re.split(f'({STRING_RESOURCE_PLACEHOLDER})', changed)
    return changed


#=====  Token level  ============

def camel_case_split(identifier, add_separator=False):
    if identifier == '\n': #TODO XXX
        return [identifier]
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    parts = [m.group(0).lower() for m in matches]
    return add_between_elements(parts, placeholders['camel_case_separator']) if add_separator else parts


def split_with_numbers(identifier, add_separator=False):
    parts = list(filter(None, re.split('(?<=[a-zA-Z0-9])?([0-9])(?=[a-zA-Z0-9]+|$)', identifier)))
    return add_between_elements(parts, placeholders['camel_case_separator']) if add_separator else parts


def split_lowercase(identifier, splitting_dict, add_separator=False):
    if identifier in splitting_dict:
        parts = splitting_dict[identifier]
    else:
        parts = [identifier]
    return add_between_elements(parts, placeholders['same_case_separator']) if add_separator else parts


def underscore_split(identifier, add_separator=False):
    #TODO it creates empty element if the identifier starts or ends with underscore
    parts = identifier.split("_")
    parts_with_separators = add_between_elements(parts,
                                                 placeholders['underscore_separator']) if add_separator else parts
    if parts_with_separators[0] == '':
        del (parts_with_separators[0])
    if parts_with_separators[-1] == '':
        del (parts_with_separators[-1])
    return parts_with_separators

#======== Token list level   =========


def filter_out_stop_words(tokens):
    STOP_WORDS = ["a", "an", "and", "are", "as", "at", "be", "for", "has", "in", "is", "it", "its", "of", "on", "that",
                  "the", "to", "was", "were", "with"]
    # the following words are normally stop words but we might want not to consider as stop words:  by, from, he, will

    return list(filter(lambda w: w not in STOP_WORDS, tokens))

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


def add_ect(token_list):
    token_list.append("<ect>")
    return token_list

def replace_infrequent_numeric_literal(token_list, context):
    try:
        frequent_tokens = context['frequent_tokens']
    except KeyError:
        logging.error("no frequent tokens attribute in preprocessing context")
        return
    for i in range(len(token_list)):
        if token_list[i] not in frequent_tokens:
            if re.fullmatch("[0-9]+", token_list[i]):
                token_list[i] = "<decnumber>"
            if re.fullmatch("0x[0-9]+", token_list[i]):
                token_list[i] = "<hexnumber>"
            if re.fullmatch("[0-9]+[l|L]", token_list[i]):
                token_list[i] = "<longnumber>"


    #======== Multitoken list level   ==========

def split_numeric_literals(multitokens):
    res = []
    for multitoken in multitokens:
        res.extend(list(filter(None, re.split(
            f'(?:^|(?<=[^a-zA-Z0-9]))({NUMBER_REGEX})(?=[^a-zA-Z0-9.]|$)',
            multitoken))))
    return res



def split_log_text_to_keywords_and_identifiers(multitoken_list):
    res = []
    for multitoken in multitoken_list:
        if multitoken not in [STRING_RESOURCE_PLACEHOLDER, VAR_PLACEHOLDER]:
            res.extend(spl_verbose([multitoken]))
        else:
            res.extend([multitoken])
    return res


def to_lower(multitoken_list):
    return [w for w in map(lambda w: w.lower() if w not in [STRING_RESOURCE_PLACEHOLDER, VAR_PLACEHOLDER] else w,
                           multitoken_list)]


def replace_variable_place_holders(multitoken_list):
    res = []
    for multitoken in multitoken_list:
        changed = re.sub('\\{\\}', VAR_PLACEHOLDER, multitoken)
        changed = re.sub('%[0-9]*[a-z]', VAR_PLACEHOLDER, changed)
        changed = re.split(f'({VAR_PLACEHOLDER})', changed)
        res.extend(changed)
    return res

def replace_4whitespaces_with_tabs(multitokens):
    return list(map(lambda x: x.replace("    ", "\t"), multitokens))

def spl(multitokens, two_char_delimiters, one_char_delimiter):
    two_char_regex = create_regex_from_token_list(two_char_delimiters)
    one_char_regex = create_regex_from_token_list(one_char_delimiter)
    return [w for spl in (map(lambda str: split_to_key_words_and_identifiers(str, two_char_regex, one_char_regex, delimiters_to_drop_verbose), multitokens))
            for w in spl]


def spl_non_verbose(multitokens):
    return spl(multitokens, two_character_tokens, one_character_tokens)


def spl_verbose(multitokens):
    '''
    doesn't remove such tokens as tabs, newlines, brackets
    '''
    return spl(multitokens,
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


def split_line_camel_case(context_line):
    return [item for identifier in context_line
            for item in camel_case_split(identifier, add_separator=True)]


def split_line_underscore(context_line):
    return [item for identifier in context_line
            for item in underscore_split(identifier, add_separator=True)]


def split_line_with_numbers(line):
    return [item for identifier in line
            for item in split_with_numbers(identifier, add_separator=True)]


def split_line_lowercase(splitting_file_location, line):
    splitting_dict = {}
    with open(splitting_file_location, 'r') as f:
        for ln in f:
            word, splitting = ln.split("|")
            splitting_dict[word] = splitting.split()

    return [item for identifier in line
            for item in split_lowercase(identifier, splitting_dict, add_separator=True)]


def newline_and_tab_remover(tokens):
    return list(filter(lambda t: t != "\n" and t != "\t", tokens))


def to_string_repr(p):
    return repr(" ".join(p))[1:-1] + " <ect>\n"

#=======  file-lines-level  ==============================

def lines_to_one_lines_with_newlines(lines):
    return [w for line in lines for w in (line, EOF)]


#==========================================================

def names_to_functions(pp_names, context):
    pps = []
    java_parser = JavaParser()
    for name in pp_names:
        if name == 'split_line_lowercase':
            pps.append(partial(split_line_lowercase, context['splitting_file_path']))
        elif name == 'java.strip_off_identifiers':
            pps.append(partial(java_parser.strip_off_identifiers, context['interesting_context_words']))
        elif name.startswith("java."):
            pps.append(partial(getattr(JavaParser, name[5:]), java_parser))
        else:
            pps.append(getattr(sys.modules[__name__], name))
    return pps


def apply_preprocessors(to_be_processed, preprocessors, context={}):
    if not preprocessors:
        return to_be_processed
    if isinstance(next(iter(preprocessors)), str):
        preprocessors = names_to_functions(preprocessors, context)
    for preprocessor in preprocessors:
        start = time.time()
        to_be_processed = preprocessor(to_be_processed)
        t = int(time.time() - start)
        if t > 0:
            logging.debug(f"{preprocessor}: {t}s")
    return to_be_processed

#=============   preprocess recepees     ======================
