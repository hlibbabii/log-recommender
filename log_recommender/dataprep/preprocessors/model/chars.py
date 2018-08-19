class NewLine(object):
    def __str__(self):
        return self.non_preprocessed_repr()

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return other.__class__ == self.__class__

    def non_preprocessed_repr(self):
        return "\n"

    def preprocessed_repr(self):
        return []


class Tab(object):
    def __str__(self):
        return self.non_preprocessed_repr()

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return other.__class__ == self.__class__

    def non_preprocessed_repr(self):
        return "\t"

    def preprocessed_repr(self):
        return []


class Backslash(object):
    def __str__(self):
        return "\\"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return other.__class__ == self.__class__


class Quote(object):
    def __str__(self):
        return "\""

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return other.__class__ == self.__class__


class MultilineCommentStart(object):
    def __str__(self):
        return "/*"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return other.__class__ == self.__class__


class MultilineCommentEnd(object):
    def __str__(self):
        return "*/"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return other.__class__ == self.__class__


class OneLineCommentStart(object):
    def __str__(self):
        return "//"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return other.__class__ == self.__class__