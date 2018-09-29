from dataprep.preprocessors.model.placeholders import placeholders


class Number(object):
    def __init__(self, parts_of_number):
        self.parts_of_number = parts_of_number

    def __str__(self):
        return self.non_preprocessed_repr()

    def __repr__(self):
        return f'{self.__class__.__name__}{self.parts_of_number}'

    def non_preprocessed_repr(self):
        return "".join([(w.non_preprocessed_repr() if isinstance(w, SpecialNumberChar) else str(w)) for w in self.parts_of_number])

    def preprocessed_repr(self):
        return [(w.preprocessed_repr() if isinstance(w, SpecialNumberChar) else str(w)) for w in self.parts_of_number]


class SpecialNumberChar(object):
    def __repr__(self):
        return f'{self.__class__.__name__}'


class E(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "e"

    def preprocessed_repr(self):
        return placeholders['e']


class L(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "l"

    def preprocessed_repr(self):
        return placeholders['long']


class F(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "f"

    def preprocessed_repr(self):
        return placeholders['float']


class D(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "d"

    def preprocessed_repr(self):
        return placeholders['double']


class DecimalPoint(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "."

    def preprocessed_repr(self):
        return placeholders['decimal_point']


class HexStart(SpecialNumberChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "0x"

    def preprocessed_repr(self):
        return placeholders['hex_start']