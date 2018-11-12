from enum import Enum, auto

from logrec.dataprep.preprocessors.model.general import ProcessableToken
from logrec.dataprep.preprocessors.model.numeric import Number
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.preprocessors.model.split import SplitRepr
from logrec.dataprep.split.bpe_encode import encode_word
from logrec.dataprep.util import insert_separators


class NgramSplittingType(Enum):
    CUSTOM = auto()
    BPE = auto()
    ONLY_NUMBERS = auto()


class NgramSplittingConfig(object):
    def __init__(self, splitting_type=None, merges_cache=None, merges=None, sc_splittings=None):
        self._splitting_type = splitting_type
        self._merges_cache = merges_cache
        self._merges = merges
        self._sc_splittings = sc_splittings

    @property
    def merges_cache(self):
        return self._merges_cache

    @property
    def merges(self):
        return self._merges

    @property
    def sc_splittings(self):
        return self._sc_splittings

    @merges.setter
    def merges(self, m):
        self._merges = m

    @merges_cache.setter
    def merges_cache(self, m):
        self._merges_cache = m

    def splitting_type(self, type):
        self._splitting_type = type

    @sc_splittings.setter
    def sc_splittings(self, s):
        self._sc_splittings = s

    def is_bpe(self):
        return self._splitting_type == NgramSplittingType.BPE

    def do_splitting(self, clazz):
        return (clazz == Number and self._splitting_type == NgramSplittingType.ONLY_NUMBERS) or \
               ((self._splitting_type == NgramSplittingType.BPE or self._splitting_type == NgramSplittingType.CUSTOM)
                and (clazz == Number or clazz == ProcessableToken))


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


def insert_borders(subwords, split_repr):
    if split_repr == SplitRepr.NONE:
        return subwords
    elif split_repr == SplitRepr.BONDERIES:
        return [placeholders['split_words_start']] + subwords + [placeholders['split_words_end']]
    elif split_repr == SplitRepr.BETWEEN_WORDS:
        return insert_separators(subwords, placeholders['same_case_separator'])
    else:
        raise AssertionError(f"Unknown split repr: {split_repr}")


def get_number_subwords(word):
    return [str(w) for w in word]


def do_same_case_splitting(token, ngramSplittingConfig, split_repr):
    word = token.non_preprocessed_repr()
    if ngramSplittingConfig.is_bpe():
        subwords = get_bpe_subwords(word, ngramSplittingConfig.merges, ngramSplittingConfig.merges_cache)
    elif isinstance(token, Number):
        subwords = get_number_subwords(word)
    elif isinstance(token, ProcessableToken):
        subwords = get_sc_subwords(token.non_preprocessed_repr(), ngramSplittingConfig.sc_splittings)
    else:
        raise AssertionError()

    return insert_borders(subwords, split_repr)
