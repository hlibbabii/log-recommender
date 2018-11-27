from logrec.dataprep.preprocessors.model.noneng import NonEng
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.preprocessors.model.word import WordStart
from logrec.dataprep.preprocessors.repr import torepr, ReprConfig
from logrec.dataprep.split.ngram import SplitRepr


class ProcessableTokenContainer(object):
    def __init__(self, subtokens):
        if isinstance(subtokens, list):
            self.subtokens = subtokens
        else:
            raise AssertionError(f"Should be list but is: {subtokens}")

    def add(self, token):
        self.subtokens.append(token)

    def get_subtokens(self):
        return self.subtokens

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.subtokens == other.subtokens

    def __repr__(self):
        return f'{self.__class__.__name__}{self.subtokens}'


class SplitContainer(ProcessableTokenContainer):
    def __init__(self, subtokens):
        subtokens[0].prefix = WordStart()
        super().__init__(subtokens)

    def empty_repr(self):
        return self.subtokens

    def __str__(self):
        return self.non_preprocessed_repr(ReprConfig.empty())

    def __repr__(self):
        return f'{self.__class__.__name__}{self.subtokens}'

    def non_preprocessed_repr(self, repr_config):
        return "".join(map(lambda s: torepr(s, repr_config), self.subtokens))
        # return "".join(map(lambda s: s.non_preprocessed_repr(repr_config) if isinstance(s, NonEng) else str(s), self.subtokens))

    def preprocessed_repr(self, repr_config):
        res = []
        for subtoken in self.subtokens:
            r = torepr(subtoken, repr_config)
            res.extend(r if isinstance(r, list) else [r])
        if repr_config.split_repr == SplitRepr.BETWEEN_WORDS:
            if res[0] != placeholders['underscore_separator']:
                del res[0]
        elif repr_config.split_repr == SplitRepr.BONDERIES:
            res.append(placeholders['split_words_end'])
        else:
            raise AssertionError("Not i mplemented")
        return res


class TextContainer(ProcessableTokenContainer):
    def __str__(self):
        return " ".join([str(s) for s in self.non_preprocessed_repr(ReprConfig.empty())])

    @classmethod
    def __calc_non_eng_percent(cls, tokens):
        total = len(tokens)
        non_eng = sum(map(lambda x: isinstance(x, NonEng), tokens))
        return float(non_eng) / total if total != 0 else 0.0, non_eng

    def __init__(self, tokens):
        super().__init__(tokens)
        self.non_eng_percent, self.non_eng_qty = self.__calc_non_eng_percent(tokens)

    def __repr__(self):
        return f'{self.__class__.__name__}{self.subtokens} %={self.non_eng_percent} N={self.non_eng_qty}'

    def has_non_eng_contents(self):
        return self.non_eng_percent > 0.2 and self.non_eng_qty >= 4

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.subtokens == other.subtokens and self.non_eng_percent == other.non_eng_percent and \
               self.non_eng_qty == other.non_eng_qty


class OneLineComment(TextContainer):
    def __init__(self, tokens):
        super().__init__(tokens)

    def non_preprocessed_repr(self, repr_config):
        if NonEng in repr_config.types_to_be_repr and self.has_non_eng_contents():
            return ["//", placeholders['non_eng_contents']]
        else:
            return ["//"] + torepr(self.subtokens, repr_config)

    def preprocessed_repr(self, repr_config):
        return placeholders['comment']


class MultilineComment(TextContainer):
    def __init__(self, tokens):
        super().__init__(tokens)

    def non_preprocessed_repr(self, repr_config):
        if NonEng in repr_config.types_to_be_repr and self.has_non_eng_contents():
            return ["//", placeholders['non_eng_contents']]
        else:
            return ["/*"] + torepr(self.subtokens, repr_config) + ["*/"]

    def preprocessed_repr(self, repr_config):
        return placeholders['comment']


class StringLiteral(TextContainer):
    def __init__(self, tokens):
        super().__init__(tokens)

    def non_preprocessed_repr(self, repr_config):
        if NonEng in repr_config.types_to_be_repr and self.has_non_eng_contents():
            return ["\"", placeholders['non_eng_contents'], "\""]
        else:
            return ["\""] + torepr(self.subtokens, repr_config) + ["\""]

    def preprocessed_repr(self, repr_config):
        return placeholders['string_literal']
