import logging
from enum import Enum
from typing import Dict, List, Type

from logrec.dataprep.model.chars import NewLine, Tab
from logrec.dataprep.model.containers import SplitContainer, StringLiteral, OneLineComment, MultilineComment
from logrec.dataprep.model.noneng import NonEngSubWord, NonEngFullWord
from logrec.dataprep.model.numeric import Number
from logrec.dataprep.model.word import SubWord, FullWord

logger = logging.getLogger(__name__)


class PrepParam(str, Enum):
    EN_ONLY: str = 'enonly'
    COM_STR: str = 'comstr'
    SPLIT: str = 'split'
    SPLIT_REPR: str = 'splitrepr'
    TABS_NEWLINES: str = 'tabsnewlines'


class PrepConfig(object):
    possible_param_values = {
        PrepParam.EN_ONLY: [0, 1],
        PrepParam.COM_STR: [0, 1, 2],
        PrepParam.SPLIT: [0, 1, 2, 3, 4, 5, 6],
        PrepParam.SPLIT_REPR: [0, 1],
        PrepParam.TABS_NEWLINES: [0, 1],
    }

    @classmethod
    def from_encoded_string(cls, s: str):
        res = {}
        for ch, pp in zip(s, PrepParam):
            res[pp] = int(ch)
        return cls(res)

    @staticmethod
    def __check_invariants(params: Dict[PrepParam, int]):
        n_expected_params = len([i for i in PrepParam])
        if len(params) != n_expected_params:
            raise ValueError(f'Expected {n_expected_params} params, got {len(params)}')
        for pp in PrepParam:
            if params[pp] not in PrepConfig.possible_param_values[pp]:
                raise ValueError(f'Invalid value {params[pp]} for prep param {pp}, '
                                 f'possible values are: {PrepConfig.possible_param_values[pp]}')

        if params[PrepParam.EN_ONLY] == 1 and params[PrepParam.SPLIT] == 0:
            raise ValueError("Combination NO_SPL=0 and EN_ONLY=1 is not supported.")

    def __init__(self, params: Dict[PrepParam, int]):
        PrepConfig.__check_invariants(params)

        self.params = params

    def str(self) -> str:
        res = ""
        for k in PrepParam:
            res += str(self.params[k])
        return res

    def get_param_value(self, param: PrepParam) -> int:
        return self.params[param]


com_str_to_types_to_be_repr = {
    0: [],
    1: [StringLiteral],
    2: [StringLiteral, OneLineComment, MultilineComment],
}


def get_types_to_be_repr(prep_config: PrepConfig) -> List[Type]:
    res = [FullWord]
    if prep_config.get_param_value(PrepParam.SPLIT) in [1, 2, 3, 4, 5, 6, 9]:
        res.extend([SplitContainer, SubWord])
    if prep_config.get_param_value(PrepParam.SPLIT) in [2, 3, 4, 5, 6, 9]:
        res.append(Number)
    res.extend(com_str_to_types_to_be_repr[prep_config.get_param_value(PrepParam.COM_STR)])
    if prep_config.get_param_value(PrepParam.TABS_NEWLINES):
        res.extend([NewLine, Tab])
    if prep_config.get_param_value(PrepParam.EN_ONLY):
        res.extend([NonEngSubWord, NonEngFullWord])
    return res
