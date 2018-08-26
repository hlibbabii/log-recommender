from functools import partial

from dataprep import base_project_dir
from dataprep.lcsplitting.lowercase_words_splitter import load_english_dict, load_non_english_dicts
from dataprep.preprocessors.model.general import ProcessableToken, ProcessableTokenContainer, NonEng
from dataprep.preprocessors.model.split import NonDelimiterSplitContainer


def isascii(str):
    return all(ord(c) < 128 for c in str)

def mark_noneng(eng_dict, non_eng_dict, token):
    str = token.get_val()
    is_non_eng = not isascii(str)
    return NonEng(str) if is_non_eng else token


def mark(token_list, context):
    eng_dict = load_english_dict(f'{base_project_dir}/dicts/eng')
    non_eng_dict = load_non_english_dicts(f'{base_project_dir}/dicts/non-eng')

    return [apply_operation_to_token(token, partial(mark_noneng, eng_dict, non_eng_dict)) for token in token_list]


def apply_operation_to_token(token, func):
    if isinstance(token, ProcessableToken):
        return func(token)
    elif isinstance(token, ProcessableTokenContainer):
        parts = []
        for subtoken in token.get_subtokens():
            parts.append(apply_operation_to_token(subtoken, func))
        if isinstance(token, NonDelimiterSplitContainer):
            return type(token)(parts, token.is_capitalized())
        else:
            return type(token)(parts)
    else:
        return token