from logrec.dataprep.model.placeholders import placeholders
from logrec.dataprep.preprocessors.repr import ReprConfig
from logrec.dataprep.split.ngram import NgramSplittingType, do_ngram_splitting


class Number(object):
    def __init__(self, parts_of_number):
        if not isinstance(parts_of_number, list):
            raise ValueError(f"Parts of number must be list but is {type(parts_of_number)}")
        self.parts_of_number = parts_of_number

    def __str__(self):
        return self.non_preprocessed_repr(ReprConfig.empty())

    def __repr__(self):
        return f'{self.__class__.__name__}{self.parts_of_number}'

    def non_preprocessed_repr(self, repr_config):
        return "".join([str(w) for w in self.parts_of_number])

    def preprocessed_repr(self, repr_config):
        if repr_config.ngram_split_config is None:
            return self.non_preprocessed_repr(repr_config)

        if repr_config.ngram_split_config.splitting_type in [NgramSplittingType.ONLY_NUMBERS,
                                                             NgramSplittingType.NUMBERS_AND_CUSTOM]:
            subwords = [str(w) for w in self.parts_of_number]
        elif repr_config.ngram_split_config.splitting_type is not None:
            subwords = do_ngram_splitting(self.non_preprocessed_repr(repr_config), repr_config.ngram_split_config)
        else:
            subwords = [self.non_preprocessed_repr(repr_config)]

        if len(subwords) > 1:
            return [placeholders['word_start']] + subwords + [placeholders['word_end']]
        else:
            return subwords

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.parts_of_number == other.parts_of_number


class SpecialNumberChar(object):
    def __repr__(self):
        return f'{self.__class__.__name__}'

    def __eq__(self, other):
        return self.__class__ == other.__class__


class E(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr(ReprConfig.empty())

    def non_preprocessed_repr(self, repr_config):
        return "e"


class L(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr(ReprConfig.empty())

    def non_preprocessed_repr(self, repr_config):
        return "l"


class F(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr(ReprConfig.empty())

    def non_preprocessed_repr(self, repr_config):
        return "f"


class D(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr(ReprConfig.empty())

    def non_preprocessed_repr(self, repr_config):
        return "d"


class DecimalPoint(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr(ReprConfig.empty())

    def non_preprocessed_repr(self, repr_config):
        return "."


class HexStart(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr(ReprConfig.empty())

    def non_preprocessed_repr(self, repr_cofig):
        return "0x"
