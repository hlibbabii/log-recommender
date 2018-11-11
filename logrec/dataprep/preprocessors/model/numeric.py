from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.util import insert_separators


class Number(object):
    def __init__(self, parts_of_number):
        self.parts_of_number = parts_of_number

    def __str__(self):
        return self.non_preprocessed_repr()

    def __repr__(self):
        return f'{self.__class__.__name__}{self.parts_of_number}'

    def non_preprocessed_repr(self):
        return "".join([str(w) for w in self.parts_of_number])

    def preprocessed_repr(self):
        subwords = [str(w) for w in self.parts_of_number]
        return insert_separators(subwords, placeholders['same_case_separator'])

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.parts_of_number == other.parts_of_number


class SpecialNumberChar(object):
    def __repr__(self):
        return f'{self.__class__.__name__}'

    def __eq__(self, other):
        return self.__class__ == other.__class__


class E(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "e"


class L(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "l"


class F(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "f"


class D(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "d"


class DecimalPoint(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "."


class HexStart(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "0x"