import logging
from enum import Enum
from typing import Dict, List, Type

from logrec.dataprep.model.chars import NewLine, Tab
from logrec.dataprep.model.containers import SplitContainer, StringLiteral, OneLineComment, MultilineComment
from logrec.dataprep.model.noneng import NonEngSubWord, NonEngFullWord
from logrec.dataprep.model.numeric import Number
from logrec.dataprep.model.word import SubWord, FullWord

logger = logging.getLogger(__name__)


class PreprocessingParam(str, Enum):
    EN_ONLY: str = 'enonly'
    NO_COM_STR: str = 'nocomstr'
    SPL: str = 'spl'
    # 0 - no_splitting
    # 1 - only camel-case, underscore splitting
    # 2 - camel-case, underscore; splitting of numbers
    # 3 - camel-case, underscore; splitting of numbers; same-case splitting
    # 4 - camel-case, underscore; byte-pair encoding (bpe), n merges: 5000
    # 5 - camel-case, underscore; byte-pair encoding (bpe), n merges: 1000
    # 6 - camel-case, underscore; byte-pair encoding (bpe), n merges: 10000
    # 9 - camel-case, underscore; byte-pair encoding (bpe), n merges: custom
    NO_SEP: str = 'nosep'
    NO_NEWLINES_TABS: str = 'nonewlinestabs'


class PrepParamsParser(object):
    @staticmethod
    def from_arg_str(prep_params_str: str) -> Dict[str, int]:
        res = {}
        for param in prep_params_str.split(','):
            key, val = param.split('=')
            res[key] = int(val)
        return res

    @staticmethod
    def from_encoded_string(s: str) -> Dict[str, int]:
        res = {}
        for ch, pp in zip(s, PreprocessingParam):
            res[pp] = int(ch)
        return res

    @staticmethod
    def encode_dict(prep_params_dict: Dict[str, int]) -> str:
        res = ""
        for k in PreprocessingParam:
            if prep_params_dict[k] is None:
                res += "_"
            else:
                res += str(int(prep_params_dict[k]))
        return res


com_str_to_types_to_be_repr = {
    0: [],
    1: [StringLiteral],
    2: [StringLiteral, OneLineComment, MultilineComment],
}


def get_types_to_be_repr(preprocessing_params: Dict[str, int]) -> List[Type]:
    res = [FullWord]
    if preprocessing_params[PreprocessingParam.SPL] in [1, 2, 3, 4, 5, 6, 9]:
        res.extend([SplitContainer, SubWord])
    if preprocessing_params[PreprocessingParam.SPL] in [2, 3, 4, 5, 6, 9]:
        res.append(Number)
    res.extend(com_str_to_types_to_be_repr[preprocessing_params[PreprocessingParam.NO_COM_STR]])
    if preprocessing_params[PreprocessingParam.NO_NEWLINES_TABS]:
        res.extend([NewLine, Tab])
    if preprocessing_params[PreprocessingParam.EN_ONLY]:
        res.extend([NonEngSubWord, NonEngFullWord])
    return res
