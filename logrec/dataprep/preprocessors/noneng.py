import logging

from logrec.dataprep import path_to_eng_dicts, path_to_non_eng_dicts
from logrec.dataprep.lang.langchecker import LanguageChecker
from logrec.dataprep.preprocessors.model.containers import ProcessableTokenContainer
from logrec.dataprep.preprocessors.model.noneng import NonEngFullWord, NonEngSubWord
from logrec.dataprep.preprocessors.model.word import FullWord, SubWord

logger = logging.getLogger(__name__)

lang_checker = LanguageChecker(path_to_eng_dicts, path_to_non_eng_dicts)

def mark(token_list, context):
    return [
        apply_operation_to_token(token, lambda t, c: c(t) if lang_checker.is_non_eng(t.get_canonic_form()) else t)
        for token in token_list]


# TODO merge this with similar function in split.py
def apply_operation_to_token(token, func):
    if isinstance(token, SubWord):
        return func(token, NonEngSubWord)
    elif isinstance(token, FullWord):
        return func(token, NonEngFullWord)
    elif isinstance(token, ProcessableTokenContainer):
        parts = []
        for subtoken in token.get_subtokens():
            parts.append(apply_operation_to_token(subtoken, func))
        return type(token)(parts)
    else:
        return token