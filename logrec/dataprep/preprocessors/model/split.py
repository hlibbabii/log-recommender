from abc import ABC, abstractmethod

from logrec.dataprep.preprocessors.model.general import ProcessableTokenContainer
from logrec.dataprep.preprocessors.model.placeholders import placeholders

from enum import Enum, auto


class SplitRepr(Enum):
    BETWEEN_WORDS = auto()
    BONDERIES = auto()
    NONE = auto()

class SplitContainer(ProcessableTokenContainer, ABC):
    def __init__(self, subtokens):
        super().__init__(subtokens)

    def empty_repr(self):
        return self.subtokens

    @abstractmethod
    def boundaries_repr(self):
        pass

    @abstractmethod
    def preprocessed_repr(self):
        pass


split_repr_func_map = {
    SplitRepr.BETWEEN_WORDS: 'preprocessed_repr',
    SplitRepr.BONDERIES: 'boundaries_repr',
    SplitRepr.NONE: 'empty_repr'
}

class UnderscoreSplit(SplitContainer):
    def __init__(self, subtokens):
        super().__init__(subtokens)

    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "_".join(map(lambda s: str(s), self.subtokens))

    def preprocessed_repr(self):
        return [w for subtoken in self.subtokens for w in (subtoken, placeholders['underscore_separator'])][:-1]

    def boundaries_repr(self):
        return [placeholders['split_words_start']] + self.subtokens + [placeholders['split_words_end']]


class NonDelimiterSplitContainer(SplitContainer, ABC):
    def __init__(self, subtokens, capitalized):
        super().__init__(subtokens)
        self.capitalized = capitalized

    def __str__(self):
        return self.non_preprocessed_repr()

    def is_capitalized(self):
        return self.capitalized

    def __repr__(self):
        return f'{self.__class__.__name__}{"(CAP)" if self.capitalized else ""}{self.subtokens}'

    def boundaries_repr(self):
        return [placeholders['split_words_start']] + (
            [placeholders['capital']] if self.capitalized else []) + self.subtokens + [placeholders['split_words_end']]


class CamelCaseSplit(NonDelimiterSplitContainer):
    def non_preprocessed_repr(self):
        capitalized_str = "".join(map(lambda s: str(s).capitalize(), self.subtokens))
        return (capitalized_str[0] if self.capitalized else capitalized_str[0].lower()) + capitalized_str[1:]

    def preprocessed_repr(self):
        return ([placeholders['capital']] if self.capitalized else []) + [w for subtoken in self.subtokens for w in (subtoken, placeholders['camel_case_separator'])][:-1]


class WithNumbersSplit(NonDelimiterSplitContainer):
    def non_preprocessed_repr(self):
        capitalized_str = "".join(map(lambda s: str(s), self.subtokens))
        return (capitalized_str[0] if self.capitalized else capitalized_str[0].lower()) + capitalized_str[1:]

    def preprocessed_repr(self):
        return ([placeholders['capital']] if self.capitalized else []) + [w for subtoken in self.subtokens for w in (subtoken, placeholders['camel_case_separator'])][:-1]


class SameCaseSplit(NonDelimiterSplitContainer):
    def non_preprocessed_repr(self):
        capitalized_str = "".join(map(lambda s: str(s), self.subtokens))
        return (capitalized_str[0] if self.capitalized else capitalized_str[0].lower()) + capitalized_str[1:]

    def preprocessed_repr(self):
        return ([placeholders['capital']] if self.capitalized else []) + [w for subtoken in self.subtokens for w in (subtoken, placeholders['same_case_separator'])][:-1]