import logging
from enum import Enum

from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
from logrec.dataprep.preprocessors.model.containers import SplitContainer, StringLiteral, OneLineComment, \
    MultilineComment
from logrec.dataprep.preprocessors.model.logging import LogStatement
from logrec.dataprep.preprocessors.model.noneng import NonEng
from logrec.dataprep.preprocessors.model.numeric import Number
from logrec.dataprep.preprocessors.model.word import SubWord, FullWord

logger = logging.getLogger(__name__)


class PreprocessingParam(str, Enum):
    EN_ONLY: str = 'enonly'
    NO_COM_STR: str = 'nocomstr'
    SPL: str = 'spl'
    # 0 - no_splitting
    # 1 - only camel-case, underscore splitting
    # 2 - camel-case, underscore; splitting of numbers
    # 3 - camel-case, underscore; splitting of numbers; same-case splitting
    # 4 - camel-case, underscore; byte-pair encoding (bpe)
    NO_SEP: str = 'nosep'
    NO_NEWLINES_TABS: str = 'nonewlinestabs'
    NO_LOGS: str = 'nologs'

com_str_to_types_to_be_repr = {
    0: [],
    1: [StringLiteral],
    2: [StringLiteral, OneLineComment, MultilineComment],
}


def parse_preprocessing_params(preprocessing_types_str):
    res = {}
    for param in preprocessing_types_str.split(','):
        key, val = param.split('=')
        res[key] = int(val)
    return res


def get_types_to_be_repr(preprocessing_params):
    res = [FullWord]
    if preprocessing_params[PreprocessingParam.SPL] in [1, 2, 3, 4]:
        res.extend([SplitContainer, SubWord])
    if preprocessing_params[PreprocessingParam.SPL] in [2, 3, 4]:
        res.append(Number)
    res.extend(com_str_to_types_to_be_repr[preprocessing_params[PreprocessingParam.NO_COM_STR]])
    if preprocessing_params[PreprocessingParam.NO_NEWLINES_TABS]:
        res.extend([NewLine, Tab])
    if preprocessing_params[PreprocessingParam.EN_ONLY]:
        res.append(NonEng)
    if preprocessing_params[PreprocessingParam.NO_LOGS]:
        res.append(LogStatement)
    return res
