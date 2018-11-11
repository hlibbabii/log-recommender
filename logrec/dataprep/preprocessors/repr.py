import logging

from logrec.dataprep.preprocessors.model.general import NonEng, ProcessableToken
from logrec.dataprep.preprocessors.model.numeric import Number
from logrec.dataprep.preprocessors.model.split import SplitContainer, split_repr_func_map, SplitRepr
from logrec.dataprep.preprocessors.model.textcontainers import TextContainer
from logrec.dataprep.preprocessors.preprocessing_types import recursive, PreprocessingParam, get_types_to_be_repr, \
    check_preprocessing_params_are_valid
from logrec.dataprep.split.ngram import do_same_case_splitting

logger = logging.getLogger(__name__)


def to_repr(preprocessing_params, token_list, aux_splitting_dicts):
    """
    Preprocesses token list according to given preprocessing params
    :param preprocessing_params: e.g. {
        PreprocessingType.SPL_TYPE: 4,
        PreprocessingType.NO_COM: False,
        PreprocessingType.NO_STR: False
        PreprocessingType.NO_NEWLINES_TABS: False',
        PreprocessingType.BSR: False
    }
    :param token_list: list of tokens to be preprocessed
    :return:
    """
    check_preprocessing_params_are_valid(preprocessing_params)

    types_to_be_repr = get_types_to_be_repr(preprocessing_params)
    splitRepr = SplitRepr.BONDERIES if preprocessing_params[PreprocessingParam.BSR] else SplitRepr.BETWEEN_WORDS
    repr_list = to_repr_list(types_to_be_repr, token_list, splitRepr, aux_splitting_dicts)
    return repr_list


def to_repr_list(types_to_be_repr, token_list, bsr, aux_splitting_dicts):
    repr_res = []
    for token in token_list:
        repr_token = to_repr_token(types_to_be_repr, token, bsr, aux_splitting_dicts)
        repr_res.extend(repr_token if isinstance(repr_token, list) else [repr_token])
    return repr_res


def to_repr_token(types_to_be_repr, token, split_repr, aux_splitting_dicts):
    clazz = type(token)
    if clazz == str:
        return token
    if clazz not in types_to_be_repr and NonEng in types_to_be_repr \
            and issubclass(clazz, TextContainer) and token.has_non_eng_contents():
        return token.non_eng_contents()
    if clazz == ProcessableToken or clazz == Number:
        return do_same_case_splitting(token, aux_splitting_dicts)

    if clazz in types_to_be_repr:
        if issubclass(clazz, SplitContainer):
            repr_func = split_repr_func_map[split_repr]
            repr = getattr(token, repr_func)()
            split_repr = SplitRepr.NONE if split_repr == SplitRepr.BONDERIES else SplitRepr.BETWEEN_WORDS
        else:
            repr = token.preprocessed_repr()
    else:
        repr = token.non_preprocessed_repr()

    if clazz in recursive:
        if isinstance(repr, list):
            return to_repr_list(types_to_be_repr, repr, split_repr, aux_splitting_dicts)
        else:
            return to_repr_token(types_to_be_repr, repr, split_repr, aux_splitting_dicts)
    else:
        return repr
