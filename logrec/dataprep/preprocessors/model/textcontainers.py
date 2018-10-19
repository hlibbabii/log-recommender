from logrec.dataprep.preprocessors.model.general import ProcessableTokenContainer, NonEng
from logrec.dataprep.preprocessors.model.placeholders import placeholders


class TextContainer(ProcessableTokenContainer):
    def __str__(self):
        return " ".join([str(s) for s in self.non_preprocessed_repr()])

    @classmethod
    def __calc_non_eng_percent(cls, tokens):
        total = len(tokens)
        non_eng = sum(map(lambda x: isinstance(x, NonEng), tokens))
        return float(non_eng) / total if total != 0 else 0.0, non_eng

    def __init__(self, tokens):
        super().__init__(tokens)
        self.non_eng_percent, self.non_eng_qty = self.__calc_non_eng_percent(tokens)

    def has_non_eng_contents(self):
        return self.non_eng_percent > 0.2 and self.non_eng_qty >= 4


class OneLineComment(TextContainer):
    def __init__(self, tokens):
        super().__init__(tokens)

    def non_preprocessed_repr(self):
        return ["//"] + self.subtokens

    def preprocessed_repr(self):
        return placeholders['comment']

    def non_eng_contents(self):
        return ["//", placeholders['non_eng_contents']]


class MultilineComment(TextContainer):
    def __init__(self, tokens):
        super().__init__(tokens)

    def non_preprocessed_repr(self):
        return ["/*"] + self.subtokens + ["*/"]

    def preprocessed_repr(self):
        return placeholders['comment']

    def non_eng_contents(self):
        return ["/*", placeholders['non_eng_contents'], "*/"]


class StringLiteral(TextContainer):
    def __init__(self, tokens):
        super().__init__(tokens)

    def non_preprocessed_repr(self):
        return ["\""] + self.subtokens + ["\""]

    def preprocessed_repr(self):
        return placeholders['string_literal']

    def non_eng_contents(self):
        return ["\"", placeholders['non_eng_contents'], "\""]
