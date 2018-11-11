import logging
from enum import Enum

from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
from logrec.dataprep.preprocessors.model.general import NonEng
from logrec.dataprep.preprocessors.model.numeric import Number
from logrec.dataprep.preprocessors.model.split import CamelCaseSplit, WithNumbersSplit, UnderscoreSplit
from logrec.dataprep.preprocessors.model.textcontainers import OneLineComment, MultilineComment, StringLiteral

logger = logging.getLogger(__name__)


class PreprocessingParam(str, Enum):
    SPL_TYPE: str = 'spl_type'
    # 0 - no_splitting
    # 1 - only camel-case, underscore splitting
    # 2 - camel-case, underscore; splitting of numbers
    # 3 - camel-case, underscore; splitting of numbers; same-case splitting
    # 4 - camel-case, underscore; byte-pair encoding (bpe)

    NO_NEWLINES_TABS: str = 'nonewlinestabs'
    NO_COM: str = 'nocom'
    NO_STR: str = 'nostr'
    EN_ONLY: str = 'en_only'
    BSR: str = 'bsr'


split_type_to_types_to_be_repr = {
    0: [],
    1: [CamelCaseSplit, UnderscoreSplit, WithNumbersSplit],
    2: [CamelCaseSplit, UnderscoreSplit, WithNumbersSplit, Number],
    3: [CamelCaseSplit, UnderscoreSplit, WithNumbersSplit, Number],
    4: [CamelCaseSplit, UnderscoreSplit, WithNumbersSplit]
}


def check_preprocessing_params_are_valid(preprocessing_params):
    if preprocessing_params[PreprocessingParam.BSR] and preprocessing_params[PreprocessingParam.SPL_TYPE] == 4:
        raise ValueError("both BSR and BPE is not supported")


def parse_preprocessing_params(preprocessing_types_str):
    res = {}
    for param in preprocessing_types_str.split(','):
        key, val = param.split('=')
        if key == PreprocessingParam.SPL_TYPE:
            res[key] = int(val)
        else:
            res[key] = bool(int(val))
    return res


def get_types_to_be_repr(preprocessing_params):
    res = []
    res.extend(split_type_to_types_to_be_repr[preprocessing_params[PreprocessingParam.SPL_TYPE]])
    if preprocessing_params[PreprocessingParam.NO_COM]:
        res.extend([OneLineComment, MultilineComment])
    if preprocessing_params[PreprocessingParam.NO_STR]:
        res.append(StringLiteral)
    if preprocessing_params[PreprocessingParam.NO_NEWLINES_TABS]:
        res.extend([NewLine, Tab])
    if preprocessing_params[PreprocessingParam.EN_ONLY]:
        res.append(NonEng)
    return res


recursive = [CamelCaseSplit, WithNumbersSplit, UnderscoreSplit, OneLineComment, MultilineComment, StringLiteral, NonEng]
