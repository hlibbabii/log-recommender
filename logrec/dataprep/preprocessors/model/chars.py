class SpecialChar(object):
    def __eq__(self, other):
        return other.__class__ == self.__class__

    def __repr__(self):
        return f'<{self.__class__.__name__}>'


class NewLine(SpecialChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "\n"

    def preprocessed_repr(self):
        return []


class Tab(SpecialChar):
    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "\t"

    def preprocessed_repr(self):
        return []


class Backslash(SpecialChar):
    def __str__(self):
        return "\\"


class Quote(SpecialChar):
    def __str__(self):
        return "\""


class MultilineCommentStart(SpecialChar):
    def __str__(self):
        return "/*"

class MultilineCommentEnd(SpecialChar):
    def __str__(self):
        return "*/"


class OneLineCommentStart(SpecialChar):
    def __str__(self):
        return "//"