from dataprep.preprocessors.model.general import ProcessableTokenContainer
from dataprep.preprocessors.model.placeholders import placeholders


class TextContainer(ProcessableTokenContainer):
    def __str__(self):
        return " ".join([str(s) for s in self.non_preprocessed_repr()])



class OneLineComment(TextContainer):
    def __init__(self, tokens):
        super().__init__(tokens)

    def non_preprocessed_repr(self):
        return ["//"] + self.subtokens

    def preprocessed_repr(self):
        return placeholders['comment']


class MultilineComment(TextContainer):
    def __init__(self, tokens):
        super().__init__(tokens)

    def non_preprocessed_repr(self):
        return ["/*"] + self.subtokens + ["*/"]

    def preprocessed_repr(self):
        return placeholders['comment']


class StringLiteral(TextContainer):
    def __init__(self, tokens):
        super().__init__(tokens)

    def non_preprocessed_repr(self):
        return ["\""] + self.subtokens + ["\""]

    def preprocessed_repr(self):
        return placeholders['string_literal']