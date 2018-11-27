from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.preprocessors.model.word import Capitalization, Word
from logrec.dataprep.preprocessors.repr import torepr


class NonEng(object):
    def __init__(self, processable_token):
        if not isinstance(processable_token, Word):
            raise ValueError(f"NonEng excepts Word but {type(processable_token)} is passed")
        self.processable_token = processable_token

    def non_preprocessed_repr(self, repr_config):
        return torepr(self.processable_token, repr_config)

    def preprocessed_repr(self, repr_config):
        res = []
        repr = torepr(self.processable_token, repr_config)
        if repr[0] in [placeholders['camel_case_separator'], placeholders['underscore_separator']]:
            res.append(repr[0])
            if repr[1] in [placeholders['capitals'], placeholders['capital']]:
                res.append(repr[1])
        else:
            if repr[0] in [placeholders['capitals'], placeholders['capital']]:
                res.append(repr[0])
        res.append(placeholders['non_eng'])
        return res

    def __repr__(self):
        return f'{self.__class__.__name__}({self.processable_token.__repr__()})'

    def __str__(self):
        return str(self.processable_token)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.processable_token == other.processable_token
