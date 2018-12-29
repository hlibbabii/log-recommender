import logging
from enum import Enum

from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
from logrec.dataprep.preprocessors.model.containers import SplitContainer, StringLiteral, OneLineComment, \
    MultilineComment
from logrec.dataprep.preprocessors.model.logging import LogStatement, LogContent, LoggableBlock
from logrec.dataprep.preprocessors.model.noneng import NonEngSubWord, NonEngFullWord
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


class PrepParamsParser(object):
    @staticmethod
    def from_arg_str(prep_params_str):
        res = {}
        for param in prep_params_str.split(','):
            key, val = param.split('=')
            res[key] = int(val)
        return res

    @staticmethod
    def from_encoded_string(str):
        res = {}
        for ch, pp in zip(str, PreprocessingParam):
            res[pp] = int(ch)
        return res

    @staticmethod
    def encode_dict(prep_params_dict):
        res = ""
        for k in PreprocessingParam:
            if prep_params_dict[k] is None:
                res += "_"
            else:
                res += str(int(prep_params_dict[k]))
        return res

    @staticmethod
    def to_classification_prep_params(st):
        nologs_pos_index = list(PreprocessingParam).index(PreprocessingParam.NO_LOGS)
        return st[:nologs_pos_index] + st[nologs_pos_index + 1:]



com_str_to_types_to_be_repr = {
    0: [],
    1: [StringLiteral],
    2: [StringLiteral, OneLineComment, MultilineComment],
}


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
        res.extend([NonEngSubWord, NonEngFullWord])
    if preprocessing_params[PreprocessingParam.NO_LOGS]:
        res.extend([LogStatement, LogContent, LoggableBlock])
    return res
