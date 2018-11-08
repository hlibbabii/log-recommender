import logging

from logrec.dataprep.preprocessors.model.general import NonEng
from logrec.dataprep.preprocessors.model.split import NonDelimiterSplitContainer, SplitContainer, split_repr_func_map, \
    SplitRepr
from logrec.dataprep.preprocessors.model.textcontainers import TextContainer
from logrec.dataprep.preprocessors.preprocessing_types import token_to_preprocessing_type_level_dict, always_repr, \
    recursive, \
    PreprocessingType

logger = logging.getLogger(__name__)

DEFAULT_NO_COM_NO_STR = {
    PreprocessingType.SPL:    True, PreprocessingType.NUM_SPL:          True, PreprocessingType.NO_COM: True,
    PreprocessingType.NO_STR: True, PreprocessingType.NO_NEWLINES_TABS: True, PreprocessingType.SC_SPL: False,
    PreprocessingType.BSR: True
}

DEFAULT_NO_COM = {
    PreprocessingType.SPL:     True, PreprocessingType.NUM_SPL:          True, PreprocessingType.NO_COM: True,
    PreprocessingType.NO_STR: False, PreprocessingType.NO_NEWLINES_TABS: True, PreprocessingType.SC_SPL: False,
    PreprocessingType.BSR: True
}

DEFAULT = {
    PreprocessingType.SPL:     True, PreprocessingType.NUM_SPL:          True, PreprocessingType.NO_COM: False,
    PreprocessingType.NO_STR: False, PreprocessingType.NO_NEWLINES_TABS: True, PreprocessingType.SC_SPL: False,
    PreprocessingType.BSR: True
}


def to_repr(preprocessing_params, token_list):
    if PreprocessingType.BSR not in preprocessing_params or preprocessing_params[PreprocessingType.BSR] is None:
        raise AssertionError('PreprocessingType.BSR should be presen twith value True or false')
    """
    Preprocesses token list according to given preprocessing params
    :param preprocessing_params: e.g. {
        PreprocessingType.SPL: True,
        PreprocessingType.NUM_SPL: True,
        PreprocessingType.NO_COM: False,
        PreprocessingType.NO_STR: False
        PreprocessingType.NO_NEWLINES_TABS: False',
        PreprocessingType.SC_SPL: True
        PreprocessingType.BSR: True
    }
    :param token_list: list of tokens to be preprocessed
    :return:
    """
    types_to_be_repr_dict = {k:preprocessing_params[v] for (k, v) in token_to_preprocessing_type_level_dict.items()
                             if v in preprocessing_params}
    splitRepr = SplitRepr.BONDERIES if preprocessing_params[PreprocessingType.BSR] else SplitRepr.BETWEEN_WORDS
    repr_list = to_repr_list(types_to_be_repr_dict, token_list, splitRepr)
    return repr_list


def to_repr_list(types_to_be_repr_dict, token_list, bsr):
    repr_res = []
    for token in token_list:
        repr_token = to_repr_token(types_to_be_repr_dict, token, bsr)
        repr_res.extend(repr_token if isinstance(repr_token, list) else [repr_token])
    return repr_res


def to_repr_token(types_to_be_repr_dict, token, split_repr):
    clazz = type(token)
    if clazz in types_to_be_repr_dict and not types_to_be_repr_dict[clazz] \
            and NonEng in types_to_be_repr_dict and types_to_be_repr_dict[NonEng] \
            and issubclass(clazz, TextContainer) and token.has_non_eng_contents():
        return token.non_eng_contents()
    elif clazz in always_repr:
        return token.to_repr()
    elif clazz in types_to_be_repr_dict:
        if types_to_be_repr_dict[clazz]:
            if issubclass(clazz, SplitContainer):
                repr_func = split_repr_func_map[split_repr]
                repr = getattr(token, repr_func)()
                split_repr = SplitRepr.NONE if split_repr == SplitRepr.BONDERIES else SplitRepr.BETWEEN_WORDS
            else:
                repr = token.preprocessed_repr()
        else:
            repr = token.non_preprocessed_repr()


        if clazz in recursive and isinstance(repr, list):
            return to_repr_list(types_to_be_repr_dict, repr, split_repr)
        elif clazz in recursive:
            return to_repr_token(types_to_be_repr_dict, repr, split_repr)
        else:
            return repr
    elif clazz in recursive:
        repr_list = to_repr_list(types_to_be_repr_dict, token.get_subtokens(), split_repr)
        if isinstance(token, NonDelimiterSplitContainer):
            return clazz(repr_list, token.is_capitalized())
        else:
            return clazz(repr_list)
    else:
        return token
