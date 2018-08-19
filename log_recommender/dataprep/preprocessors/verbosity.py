from dataprep.preprocessors.model.chars import NewLine, Tab
from dataprep.preprocessors.model.general import ProcessableToken
from dataprep.preprocessors.model.numeric import Number
from dataprep.preprocessors.model.split import CamelCaseSplit, WithNumbersSplit, UnderscoreSplit
from dataprep.preprocessors.model.textcontainers import OneLineComment, MultilineComment, StringLiteral

preprocessing_verbosity_params = [
    "splitting_done",
    "sc_splitting_done",
    "number_splitting_done",
    "comments_str_literals_obfuscated",
    "new_lines_and_tabs_removed"
]

token_to_verbosity_level_dict = {
    CamelCaseSplit: 'splitting_done',
    WithNumbersSplit: 'splitting_done',
    UnderscoreSplit: 'splitting_done',
    Number: 'number_splitting_done',
    OneLineComment: 'comments_str_literals_obfuscated',
    MultilineComment: 'comments_str_literals_obfuscated',
    StringLiteral: 'comments_str_literals_obfuscated',
    NewLine: 'new_lines_and_tabs_removed',
    Tab: 'new_lines_and_tabs_removed'
}

recursive = [CamelCaseSplit, WithNumbersSplit, UnderscoreSplit, OneLineComment, MultilineComment, StringLiteral]
always_repr = [ProcessableToken]