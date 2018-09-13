from enum import Enum

from dataprep.preprocessors.model.chars import NewLine, Tab
from dataprep.preprocessors.model.general import ProcessableToken
from dataprep.preprocessors.model.numeric import Number
from dataprep.preprocessors.model.split import CamelCaseSplit, WithNumbersSplit, UnderscoreSplit, SameCaseSplit
from dataprep.preprocessors.model.textcontainers import OneLineComment, MultilineComment, StringLiteral


class PreprocessingType(Enum):
    SPL = 'spl'
    SC_SPL = 'scspl'
    NUM_SPL = 'numspl'
    NO_STR = 'nostr'
    NO_COM = 'nocom'
    NO_NEWLINES_TABS = 'nonewlinestabs'


token_to_preprocessing_type_level_dict = {
    CamelCaseSplit: PreprocessingType.SPL,
    WithNumbersSplit: PreprocessingType.SPL,
    UnderscoreSplit: PreprocessingType.SPL,
    SameCaseSplit: PreprocessingType.SC_SPL,
    Number: PreprocessingType.NUM_SPL,
    OneLineComment: PreprocessingType.NO_COM,
    MultilineComment: PreprocessingType.NO_COM,
    StringLiteral: PreprocessingType.NO_STR,
    NewLine: PreprocessingType.NO_NEWLINES_TABS,
    Tab: PreprocessingType.NO_NEWLINES_TABS
}

def get_preprocessing_types_set():
    return list(set(token_to_preprocessing_type_level_dict.values()))

recursive = [SameCaseSplit, CamelCaseSplit, WithNumbersSplit, UnderscoreSplit, OneLineComment, MultilineComment, StringLiteral]
always_repr = [ProcessableToken]