from enum import Enum, auto

from logrec.dataprep.preprocessors.model.general import ProcessableToken, NonEng
from logrec.dataprep.preprocessors.model.numeric import Number
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.split.bpe_encode import encode_word
from logrec.dataprep.util import insert_separators


class NgramSplittingType(Enum):
    CUSTOM = auto()
    BPE = auto()


def get_bpe_subwords(word, merges, cache):
    if word in cache:
        return cache[word]
    else:
        return encode_word(word, merges)


def get_sc_subwords(word, splittings):
    if word in splittings:
        return splittings[word]
    else:
        return [word]


def do_same_case_splitting(token, aux_splitting_dicts):
    if 'ngramSplittingType' not in aux_splitting_dicts:
        return token
    ngramSplittingType = aux_splitting_dicts['ngramSplittingType']
    if ngramSplittingType == NgramSplittingType.BPE:
        if isinstance(token, ProcessableToken):
            word = token.to_repr()
        elif isinstance(token, Number):
            word = token.non_preprocessed_repr()
        elif isinstance(token, NonEng):
            word = token.non_preprocessed_repr()
        else:
            raise AssertionError()
        subwords = get_bpe_subwords(word, aux_splitting_dicts['merges'], aux_splitting_dicts['merges_cache'])
        return insert_separators(subwords, placeholders['same_case_separator'])
    elif ngramSplittingType == NgramSplittingType.CUSTOM:
        if isinstance(token, ProcessableToken):
            subwords = get_sc_subwords(token.to_repr(), aux_splitting_dicts['sc_splittings'])
            return insert_separators(subwords, placeholders['same_case_separator'])
        elif isinstance(token, NonEng):
            subwords = get_sc_subwords(token.non_preprocessed_repr(), aux_splitting_dicts['sc_splittings'])
            return insert_separators(subwords, placeholders['same_case_separator'])
        elif isinstance(token, Number):
            return token.preprocessed_repr()
        else:
            raise AssertionError()
    else:
        raise AssertionError(f"NgramSplittingType {ngramSplittingType} is not supproted ")
