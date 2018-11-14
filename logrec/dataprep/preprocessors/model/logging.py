from logrec.dataprep.preprocessors.model.general import ProcessableTokenContainer, ProcessableToken
from logrec.dataprep.preprocessors.model.placeholders import placeholders


class LogStatement(object):
    def __init__(self, object_name=None, method_name=None,
                 log_content_token_list=None, tokens_before_final_semicolon=None):
        self._object_name = object_name
        self._method_name = method_name
        self._log_content = LogContent(log_content_token_list if log_content_token_list is not None else [])
        self._tokens_before_final_semicolon = (tokens_before_final_semicolon
                                               if tokens_before_final_semicolon is not None else [])

    @property
    def object_name(self):
        return self._object_name

    @property
    def method_name(self):
        return self._method_name

    @object_name.setter
    def object_name(self, name):
        self._object_name = name

    @method_name.setter
    def method_name(self, name):
        self._method_name = name

    def add_to_log_content(self, token):
        self._log_content.add(token)

    def add_to_tokens_before_final_semicolon(self, token):
        self._tokens_before_final_semicolon.append(token)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.object_name}#{self.method_name}){self._log_content}{self._tokens_before_final_semicolon}'

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self._object_name == other._object_name \
               and self._method_name == other._method_name and self._log_content == other._log_content \
               and self._tokens_before_final_semicolon == other._tokens_before_final_semicolon

    def non_preprocessed_repr(self):
        return [ProcessableToken(self._object_name), '.', ProcessableToken(self._method_name), '('] \
               + self._log_content.get_subtokens() + [')'] + self._tokens_before_final_semicolon + [';']

    def preprocessed_repr(self):
        return placeholders['log_statement']


class LogContent(ProcessableTokenContainer):
    def __init__(self, log_content_token_list):
        super().__init__(log_content_token_list)
