from enum import Enum

from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
from logrec.dataprep.preprocessors.model.general import ProcessableToken, NonEng
from logrec.dataprep.preprocessors.model.numeric import Number
from logrec.dataprep.preprocessors.model.split import CamelCaseSplit, WithNumbersSplit, UnderscoreSplit, SameCaseSplit
from logrec.dataprep.preprocessors.model.textcontainers import OneLineComment, MultilineComment, StringLiteral


class PreprocessingType(str, Enum):
    SPL: str = 'spl'
    SC_SPL: str = 'scspl'
    NUM_SPL: str = 'numspl'
    NO_STR: str = 'nostr'
    NO_COM: str = 'nocom'
    NO_NEWLINES_TABS: str = 'nonewlinestabs'
    EN_ONLY: str = 'en_only'


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
    Tab: PreprocessingType.NO_NEWLINES_TABS,
    NonEng: PreprocessingType.EN_ONLY,
}

recursive = [SameCaseSplit, CamelCaseSplit, WithNumbersSplit, UnderscoreSplit, OneLineComment, MultilineComment, StringLiteral]
always_repr = [ProcessableToken]  # types that are resolved even if prep param set is empty
