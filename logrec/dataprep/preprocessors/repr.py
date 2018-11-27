import logging

from logrec.dataprep.split.ngram import NgramSplitConfig, SplitRepr

logger = logging.getLogger(__name__)


class ReprConfig(object):
    def __init__(self, types_to_be_repr, ngram_split_config, split_repr):
        self.types_to_be_repr = types_to_be_repr
        self.ngram_split_config = ngram_split_config
        self.split_repr = split_repr

    @classmethod
    def empty(cls):
        return cls([], NgramSplitConfig(), SplitRepr.NONE)


def to_repr_list(token_list, repr_config):
    repr_res = []
    for token in token_list:
        repr_token = torepr(token, repr_config)
        repr_res.extend(repr_token if isinstance(repr_token, list) else [repr_token])
    return repr_res


def torepr(token, repr_config):
    clazz = type(token)
    if clazz.__name__ == 'ParseableToken':
        raise AssertionError(f"Parseable token cannot be present in the final parsed model: {token}")
    if clazz == list:
        return to_repr_list(token, repr_config)
    if clazz == str:
        return token

    if clazz in repr_config.types_to_be_repr:
        return token.preprocessed_repr(repr_config)
    else:
        return token.non_preprocessed_repr(repr_config)
