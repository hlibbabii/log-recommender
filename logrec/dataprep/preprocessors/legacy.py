import logging
import re

#################   Multitoken list  level    #######
from logrec.dataprep.preprocessors import java
from logrec.dataprep.preprocessors.general import spl, spl_verbose
from logrec.dataprep.preprocessors.model.placeholders import placeholders

logger = logging.getLogger(__name__)


def replace_variable_place_holders(multitoken_list):
    res = []
    for multitoken in multitoken_list:
        changed = re.sub('\\{\\}', placeholders['var'], multitoken)
        changed = re.sub('%[0-9]*[a-z]', placeholders['var'], changed)
        changed = re.split(f'({placeholders["var"]})', changed)
        res.extend(changed)
    return res

def spl_non_verbose(multitokens, context):
    return spl(multitokens, java.multiline_comments_tokens, java.two_character_tokens, java.one_character_tokens)


def split_log_text_to_keywords_and_identifiers(multitoken_list):
    res = []
    for multitoken in multitoken_list:
        if multitoken not in [placeholders['string_resource'], placeholders['var']]:
            res.extend(spl_verbose([multitoken]))
        else:
            res.extend([multitoken])
    return res


def to_lower(multitoken_list, context):
    return [w for w in map(lambda w: w.lower() if w not in [placeholders['string_resource'], placeholders['var']] else w,
                           multitoken_list)]



def filter_out_1_and_2_char_tokens(tokens):
    return list(filter(lambda x: x not in java.one_character_tokens
                                 and x not in java.two_character_tokens
                                 and x not in java.multiline_comments_tokens, tokens))

#################    Multitoken level    ############

def remove_placeholders(multitoken, context):
    multitoken = re.sub(placeholders['var'], r'', multitoken)
    multitoken = re.sub(placeholders['string_resource'], r'', multitoken)
    return multitoken


def replace_string_resources_names(multitoken, context):
    changed = re.sub('^([0-9a-zA-Z]+\\.)+[0-9a-zA-Z]+$', placeholders['string_resource'], multitoken)
    changed = re.split(f'({placeholders["string_resource"]})', changed)
    return changed

def strip_line(multitoken):
    return multitoken.strip()

##################   Token list level    ############


def filter_out_stop_words(tokens):
    STOP_WORDS = ["a", "an", "and", "are", "as", "at", "be", "for", "has", "in", "is", "it", "its", "of", "on", "that",
                  "the", "to", "was", "were", "with"]
    # the following words are normally stop words but we might want not to consider as stop words:  by, from, he, will

    return list(filter(lambda w: w not in STOP_WORDS, tokens))

def merge_tabs(tokens, context):
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


def add_ect(token_list, context):
    token_list.append(placeholders['ect'])
    return token_list


################     Token level         ###########33

def replace_infrequent_numeric_literal(token_list, context):
    try:
        frequent_tokens = context['frequent_tokens']
    except KeyError:
        logger.error("no frequent tokens attribute in preprocessing context")
        return
    for i in range(len(token_list)):
        if token_list[i] not in frequent_tokens:
            if re.fullmatch("[0-9]+", token_list[i]):
                token_list[i] = "<decnumber>"
            if re.fullmatch("0x[0-9]+", token_list[i]):
                token_list[i] = "<hexnumber>"
            if re.fullmatch("[0-9]+[l|L]", token_list[i]):
                token_list[i] = "<longnumber>"