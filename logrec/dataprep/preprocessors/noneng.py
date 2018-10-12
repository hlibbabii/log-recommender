from logrec.dataprep import path_to_eng_dicts, path_to_non_eng_dicts
from logrec.dataprep.lang.noneng_stats_calculator import LanguageChecker
from logrec.dataprep.preprocessors.model.general import ProcessableToken, ProcessableTokenContainer, NonEng
from logrec.dataprep.preprocessors.model.split import NonDelimiterSplitContainer

lang_checker = LanguageChecker(path_to_eng_dicts, path_to_non_eng_dicts)

def mark(token_list, context):
    return [
        apply_operation_to_token(token, lambda t: NonEng(t.get_val()) if lang_checker.is_non_eng(t.get_val()) else t)
        for token in token_list]


# TODO merge this with similar function in split.py
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