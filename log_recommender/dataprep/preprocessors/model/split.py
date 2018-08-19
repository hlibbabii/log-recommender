from dataprep.preprocessors.model.general import ProcessableTokenContainer
from dataprep.preprocessors.model.placeholders import placeholders


class SplitContainer(ProcessableTokenContainer):
    def __init__(self, subtokens):
        super().__init__(subtokens)


class UnderscoreSplit(SplitContainer):
    def __init__(self, subtokens):
        super().__init__(subtokens)

    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        return "_".join(map(lambda s: str(s), self.subtokens))

    def preprocessed_repr(self):
        return [w for subtoken in self.subtokens for w in (subtoken, placeholders['underscore_separator'])][:-1]


class NonDelimiterSplitContainer(SplitContainer):
    def __init__(self, subtokens, capitalized):
        super().__init__(subtokens)
        self.capitalized = capitalized

    def __str__(self):
        return self.non_preprocessed_repr()

    def non_preprocessed_repr(self):
        capitalized_str = "".join(map(lambda s: str(s).capitalize(), self.subtokens))
        return (capitalized_str[0] if self.capitalized else capitalized_str[0].lower()) + capitalized_str[1:]

    def preprocessed_repr(self):
        return ([placeholders['capital']] if self.capitalized else []) + [w for subtoken in self.subtokens for w in (subtoken, placeholders['camel_case_separator'])][:-1]

    def is_capitalized(self):
        return self.capitalized


class CamelCaseSplit(NonDelimiterSplitContainer):
    pass

class WithNumbersSplit(NonDelimiterSplitContainer):
    pass