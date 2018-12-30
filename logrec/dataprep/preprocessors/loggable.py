import logging
from typing import List

from logrec.dataprep.preprocessors.model.logging import LoggableBlock
from logrec.dataprep.preprocessors.model.word import FullWord
from logrec.dataprep.preprocessors.preprocessing_types import PrepParamsParser
from logrec.dataprep.split.ngram import NgramSplitConfig
from logrec.dataprep.to_repr import to_repr

logger = logging.getLogger(__name__)


def to_repr_l(lst):
    return to_repr(PrepParamsParser.from_arg_str('enonly=0,nocomstr=0,spl=0,nosep=1,nonewlinestabs=0,nologs=0'), lst,
                   NgramSplitConfig())

class State(object):
    pass


class WaitingForClassDefinition(State):
    def on_open_bracket(self, block_nestedness: List[int], new_tokens: list) -> (State, list):
        block_nestedness.append(0)
        new_tokens.append('{')
        return NonLoggable(), new_tokens

    def on_closing_bracket(self, block_nestedness: List[int], new_tokens: list) -> (State, list):
        raise ValueError(f"Closing bracket is not possible here: {to_repr_l(new_tokens)}")

    def on_class_declaration(self, block_nestedness: List[int], new_tokens: list, token: str) -> (State, list):
        raise ValueError(f"Closing bracket is not possible here: {to_repr_l(new_tokens)}!")


class Loggable(State):
    def _check_state_invariant(self, block_nestedness: List[int]) -> None:
        if not block_nestedness or block_nestedness[-1] == 0:
            raise AssertionError(f'Wrong block nestedness at this state: {block_nestedness}')

    def on_open_bracket(self, block_nestedness: List[int], new_tokens: list) -> (State, list):
        self._check_state_invariant(block_nestedness)

        block_nestedness[-1] += 1
        new_tokens[-1].add('{')
        return Loggable(), new_tokens

    def on_closing_bracket(self, block_nestedness: List[int], new_tokens: list) -> (State, list):
        self._check_state_invariant(block_nestedness)

        block_nestedness[-1] -= 1
        new_tokens[-1].add('}')
        if block_nestedness[-1] > 0:
            return Loggable(), new_tokens
        else:
            return NonLoggable(), new_tokens

    def on_class_declaration(self, block_nestedness: List[int], new_tokens: list, token: str) -> (State, list):
        self._check_state_invariant(block_nestedness)

        new_tokens.append(token)
        return WaitingForClassDefinition(), new_tokens


class NonLoggable(State):
    def _check_state_invariant(self, block_nestedness: List[int]) -> None:
        if block_nestedness and block_nestedness[-1] > 0:
            raise AssertionError(f'Wrong block nestedness at this state: {block_nestedness}')

    def on_open_bracket(self, block_nestedness: List[int], new_tokens: list) -> (State, list):
        self._check_state_invariant(block_nestedness)

        if not block_nestedness:
            logger.warning(f"Strange location of opening bracket: {to_repr_l(new_tokens[-20:])}")
            block_nestedness.append(0)
            new_tokens.append('{')
            return NonLoggable(), new_tokens
        else:
            block_nestedness[-1] += 1
            new_tokens.append(LoggableBlock(['{']))
            return Loggable(), new_tokens

    def on_closing_bracket(self, block_nestedness: List[int], new_tokens: list) -> (State, list):
        self._check_state_invariant(block_nestedness)

        if not block_nestedness:
            raise ValueError(f"Closing bracket is not possible here: {to_repr_l(new_tokens)}")

        if block_nestedness[-1] == 0:
            del block_nestedness[-1]
        else:
            block_nestedness[-1] -= 1

        if block_nestedness and block_nestedness[-1] > 0:
            new_tokens.append(LoggableBlock(['}']))
            return Loggable(), new_tokens
        else:
            new_tokens.append('}')
            return NonLoggable(), new_tokens

    def on_class_declaration(self, block_nestedness: List[int], new_tokens: list, token: str) -> (State, list):
        self._check_state_invariant(block_nestedness)

        new_tokens.append(token)
        return WaitingForClassDefinition(), new_tokens


def is_class_like_declaration(token, new_tokens):
    if not token in [FullWord.of('class'),
                     FullWord.of('enum'),
                     FullWord.of('interface')]:
        return False

    if new_tokens:
        if new_tokens[-1] == '.':
            return False
        if isinstance(new_tokens[-1], LoggableBlock) and new_tokens[-1].get_subtokens()[-1] == '.':
            return False

    return True

def mark(token_list, context):
    new_tokens = []
    block_nestedness = []
    state = NonLoggable()
    for token in token_list:
        try:
            if token == '{':
                state, new_tokens = state.on_open_bracket(block_nestedness, new_tokens)
            elif token == '}':
                state, new_tokens = state.on_closing_bracket(block_nestedness, new_tokens)
            elif is_class_like_declaration(token, new_tokens):
                state, new_tokens = state.on_class_declaration(block_nestedness, new_tokens, token)
            elif isinstance(state, Loggable):
                new_tokens[-1].add(token)
            else:
                new_tokens.append(token)
        except ValueError as ex:
            logger.warning(ex)
            return token_list
    return new_tokens
