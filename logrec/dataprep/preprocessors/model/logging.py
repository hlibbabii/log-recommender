from logrec.dataprep.preprocessors.model.containers import ProcessableTokenContainer
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.preprocessors.repr import torepr


class LogLevel(object):
    def __init__(self, value, repr):
        self._value = value
        self._repr = repr

    @property
    def value(self):
        return self._value

    @property
    def repr(self):
        return self._repr

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__

    def __repr__(self):
        return self._repr


TRACE = LogLevel(0, '`trace')
DEBUG = LogLevel(1, '`debug')
INFO = LogLevel(2, '`info')
WARN = LogLevel(3, '`warn')
ERROR = LogLevel(4, '`error')
FATAL = LogLevel(5, '`fatal')
UNKNOWN = LogLevel(100, '`unknown')


class LogStatement(object):
    def __init__(self, object_name=None, method_name=None, level=None,
                 log_content_token_list=None, tokens_before_final_semicolon=None):
        self._object_name = object_name
        self._method_name = method_name
        self._level = level
        self._log_content = LogContent(log_content_token_list if log_content_token_list is not None else [])
        self._tokens_before_final_semicolon = (tokens_before_final_semicolon
                                               if tokens_before_final_semicolon is not None else [])

    def get_log_content_tokens(self):
        return self._log_content.subtokens

    def set_log_content(self, s):
        self._log_content = LogContent(s)

    @property
    def object_name(self):
        return self._object_name

    @property
    def method_name(self):
        return self._method_name

    @property
    def level(self):
        return self._level

    @object_name.setter
    def object_name(self, name):
        self._object_name = name

    @method_name.setter
    def method_name(self, name):
        self._method_name = name

    @level.setter
    def level(self, level):
        self._level = level

    def add_to_log_content(self, token):
        self._log_content.add(token)

    def add_to_tokens_before_final_semicolon(self, token):
        self._tokens_before_final_semicolon.append(token)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.object_name}#{self.method_name}({self.level})){self._log_content}{self._tokens_before_final_semicolon}'

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__

    def non_preprocessed_repr(self, repr_config):
        return [torepr(self._object_name, repr_config), '.',
                torepr(self._method_name, repr_config), '('] \
               + torepr(self._log_content.get_subtokens(), repr_config) + [')'] \
               + torepr(self._tokens_before_final_semicolon, repr_config) + [';']

    def preprocessed_repr(self, repr_config):
        return [placeholders['log_statement'], str(self.level), placeholders['log_statement_end']]


class LogContent(ProcessableTokenContainer):
    def __init__(self, log_content_token_list):
        super().__init__(log_content_token_list)


class LoggableBlock(ProcessableTokenContainer):
    def __init__(self, content):
        super().__init__(content)

    def non_preprocessed_repr(self, repr_config):
        return torepr(self.subtokens, repr_config)

    def preprocessed_repr(self, repr_config):
        return [placeholders['loggable_block']] + torepr(self.subtokens, repr_config) + [
            placeholders['loggable_block_end']]
