class SpecialChar(object):
    def __eq__(self, other):
        return other.__class__ == self.__class__

    def __repr__(self):
        return f'<{self.__class__.__name__}>'

    def __str__(self):
        return self.non_preprocessed_repr()


class NewLine(SpecialChar):
    def non_preprocessed_repr(self):
        return "\n"

    def preprocessed_repr(self):
        return []


class Tab(SpecialChar):
    def non_preprocessed_repr(self):
        return "\t"

    def preprocessed_repr(self):
        return []


class Backslash(SpecialChar):
    def non_preprocessed_repr(self):
        return "\\"


class Quote(SpecialChar):
    def non_preprocessed_repr(self):
        return "\""


class MultilineCommentStart(SpecialChar):
    def non_preprocessed_repr(self):
        return "/*"

class MultilineCommentEnd(SpecialChar):
    def non_preprocessed_repr(self):
        return "*/"


class OneLineCommentStart(SpecialChar):
    def non_preprocessed_repr(self):
        return "//"