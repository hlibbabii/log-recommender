import re
from enum import Enum, auto

from logrec.dataprep.preprocessors.model.chars import SpecialChar
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.preprocessors.repr import ReprConfig
from logrec.dataprep.split.ngram import do_ngram_splitting, insert_borders, SplitRepr, NgramSplittingType


class Capitalization(Enum):
    UNDEFINED = auto()
    NONE = auto()
    FIRST_LETTER = auto()
    ALL = auto()


class Prefix(SpecialChar):
    @classmethod
    def of(cls, s, prefix_if_no_underscore):
        match_obj = re.fullmatch("^(_*)(.*)$", s)
        if match_obj[1] == '':
            prefix = prefix_if_no_underscore
        else:
            prefix = Underscore(match_obj[1])
        return prefix, match_obj[2]


class WordStart(Prefix):
    def __str__(self):
        return ""

    def preprocessed_repr(self, repr_config):
        return [placeholders['camel_case_separator']]


class FullWordPrefix(Prefix):
    def __str__(self):
        return ""

    def preprocessed_repr(self, repr_config):
        return []


WORD_START_INSTANCE = WordStart()


class Underscore(Prefix):
    def __init__(self, val):
        "val can be _ or ___ or _______"
        super().__init__()
        self.val = val

    def __eq__(self, other):
        return other.__class__ == self.__class__ and self.val == other.val

    def __str__(self):
        return self.val

    def preprocessed_repr(self, repr_config):
        return [placeholders['underscore_separator']]


class ZeroPrefix(Prefix):
    def __str__(self):
        return ""

    def preprocessed_repr(self, repr_config):
        return [placeholders['camel_case_separator']]


class Word(object):
    """
    Invariants:
    str === str(Word.of(str))
    """

    def __init__(self, canonic_form, capitalization=Capitalization.UNDEFINED, prefix=None):
        Word._check_canonic_form_is_valid(canonic_form)

        self.canonic_form = canonic_form
        self.capitalization = capitalization
        self.prefix = prefix

    def get_canonic_form(self):
        return self.canonic_form

    @staticmethod
    def _is_strictly_upper(s):
        return s.isupper() and not s.lower().isupper()

    @staticmethod
    def _check_canonic_form_is_valid(canonic_form):
        if not isinstance(canonic_form, str) or Word._is_strictly_upper(canonic_form) \
                or (canonic_form and Word._is_strictly_upper(canonic_form[0])):
            raise AssertionError(f"Bad canonic form: {canonic_form}")

    def __str__(self):
        return self.non_preprocessed_repr(ReprConfig.empty())

    def preprocessed_repr(self, repr_config):
        prefix_repr = self.prefix.preprocessed_repr(repr_config)
        if repr_config.ngram_split_config.splitting_type is not None and repr_config.ngram_split_config.splitting_type != NgramSplittingType.ONLY_NUMBERS:
            subwords = do_ngram_splitting(self.canonic_form, repr_config.ngram_split_config)
            subwords_with_separators = insert_borders(subwords, repr_config.split_repr)
        else:
            subwords = subwords_with_separators = [self.canonic_form]
        if self.capitalization == Capitalization.UNDEFINED or self.capitalization == Capitalization.NONE:
            res = prefix_repr + subwords_with_separators
        elif self.capitalization == Capitalization.FIRST_LETTER:
            res = prefix_repr + (
                [placeholders['capital']] if self.prefix != ZeroPrefix() else []) + subwords_with_separators
        elif self.capitalization == Capitalization.ALL:
            res = prefix_repr + [placeholders['capitals']] + subwords_with_separators
        else:
            raise AssertionError(f"Unknown value: {self.capitalization}")

        # TODO duplication below
        if self.prefix == FullWordPrefix() and repr_config.split_repr == SplitRepr.BONDERIES and len(subwords) > 1:
            return [placeholders['camel_case_separator']] + res + [placeholders['split_words_end']]
        else:
            return res

    def non_preprocessed_repr(self, repr_config):
        if self.capitalization == Capitalization.UNDEFINED or self.capitalization == Capitalization.NONE:
            return str(self.prefix) + self.canonic_form
        elif self.capitalization == Capitalization.FIRST_LETTER:
            return str(self.prefix) + self.canonic_form.capitalize()
        elif self.capitalization == Capitalization.ALL:
            return str(self.prefix) + self.canonic_form.upper()
        else:
            raise AssertionError(f"Unknown value: {self.capitalization}")

    def __repr__(self):
        return f'{self.__class__.__name__}({self.canonic_form, self.capitalization, self.prefix})'

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.canonic_form == other.canonic_form \
               and self.capitalization == other.capitalization and self.prefix == other.prefix

    @classmethod
    def from_multiple_tokens(cls, s):
        return cls.from_subword(s)

    @classmethod
    def from_subword(cls, s, prefix_if_no_underscore=ZeroPrefix()):
        prefix, s = Prefix.of(s, prefix_if_no_underscore)
        if s.islower() or not s:
            return cls(s, Capitalization.NONE, prefix)
        elif s.isupper() and len(s) > 1:
            return cls(s.lower(), Capitalization.ALL, prefix)
        elif s[0].isupper():
            return cls(s[0].lower() + s[1:], Capitalization.FIRST_LETTER, prefix)
        else:
            return cls(s, Capitalization.UNDEFINED, prefix)


class FullWord(Word):
    def __init__(self, canonic_form, capitalization=Capitalization.UNDEFINED, prefix=None):
        super().__init__(canonic_form, capitalization, prefix)

    @classmethod
    def of(cls, s):
        return FullWord.from_subword(s, FullWordPrefix())


class SubWord(Word):
    def __init__(self, canonic_form, capitalization=Capitalization.UNDEFINED, prefix=None):
        super().__init__(canonic_form, capitalization, prefix)

    @classmethod
    def of(cls, s):
        return SubWord.from_subword(s)


class ParseableToken(object):
    """
    This class represents parts of input that still needs to be parsed
    """

    def __init__(self, val):
        if not isinstance(val, str):
            raise ValueError(f"val should be str but is {type(val)}")
        self.val = val

    def __str__(self):
        return self.val

    def __repr__(self):
        return f'{self.__class__.__name__}({self.val})'

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.val == other.val
