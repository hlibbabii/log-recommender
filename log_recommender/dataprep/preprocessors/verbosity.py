from dataprep.preprocessors.model.chars import NewLine, Tab
from dataprep.preprocessors.model.general import ProcessableToken
from dataprep.preprocessors.model.numeric import Number
from dataprep.preprocessors.model.split import CamelCaseSplit, WithNumbersSplit, UnderscoreSplit
from dataprep.preprocessors.model.textcontainers import OneLineComment, MultilineComment, StringLiteral

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

verb_params_short_names = {
    'splitting_done': 'spl',
    'number_splitting_done': 'numspl',
    'comments_str_literals_obfuscated': 'nostrcom',
    'new_lines_and_tabs_removed': 'nonewlinestabs'
}

def get_all_verbosity_params():
    return list(set(token_to_verbosity_level_dict.values()))

recursive = [CamelCaseSplit, WithNumbersSplit, UnderscoreSplit, OneLineComment, MultilineComment, StringLiteral]
always_repr = [ProcessableToken]