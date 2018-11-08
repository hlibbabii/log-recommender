import logging
from enum import Enum

from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
from logrec.dataprep.preprocessors.model.general import ProcessableToken, NonEng
from logrec.dataprep.preprocessors.model.numeric import Number
from logrec.dataprep.preprocessors.model.split import CamelCaseSplit, WithNumbersSplit, UnderscoreSplit, SameCaseSplit
from logrec.dataprep.preprocessors.model.textcontainers import OneLineComment, MultilineComment, StringLiteral

logger = logging.getLogger(__name__)

class PreprocessingType(str, Enum):
    SPL: str = 'spl'
    NUM_SPL: str = 'numspl'
    SC_SPL: str = 'scspl'
    NO_NEWLINES_TABS: str = 'nonewlinestabs'
    NO_COM: str = 'nocom'
    NO_STR: str = 'nostr'
    EN_ONLY: str = 'en_only'
    BSR: str = 'bsr'


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
