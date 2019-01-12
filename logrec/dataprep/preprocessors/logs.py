import re
from enum import Enum, auto

from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
from logrec.dataprep.preprocessors.model.logging import LogStatement, LogLevel, TRACE, FATAL, ERROR, WARN, INFO, DEBUG, \
    UNKNOWN
from logrec.dataprep.preprocessors.model.word import Word

LOGGER_REGEX = re.compile("[Ll]og|LOG|[Ll]ogger|LOGGER")

TRACE_OPTIONS = '[Tt]race|TRACE|v|t|logV|[Ff]inest|FINEST'
DEBUG_OPTIONS = '[Dd]ebug|DEBUG|d|logD|[Ff]iner|FINER|[Cc]onfig|CONFIG'
INFO_OPTIONS = '[Ii]nfo|INFO|i|logI|[Ff]ine|FINE'
WARN_OPTIONS = '[Ww]arn|WARN|[Ww]arning|WARNING|w|logW'
ERROR_OPTIONS = '[Ee]rror|ERROR|e|logE'
FATAL_OPTIONS = '[Ff]atal|FATAL|[Ss]evere|SEVERE|s|f'


class LevelMatcher():
    def __init__(self, log_level: LogLevel, regex: str):
        self._log_level = log_level
        self._regex = re.compile(regex)

    def is_match(self, s: str) -> bool:
        return bool(self._regex.fullmatch(s))

    @property
    def log_level(self):
        return self._log_level


level_matchers = [
    LevelMatcher(TRACE, TRACE_OPTIONS),
    LevelMatcher(DEBUG, DEBUG_OPTIONS),
    LevelMatcher(INFO, INFO_OPTIONS),
    LevelMatcher(WARN, WARN_OPTIONS),
    LevelMatcher(ERROR, ERROR_OPTIONS),
    LevelMatcher(FATAL, FATAL_OPTIONS)
]


def get_log_level(token_str: str) -> LogLevel:
    for level_matcher in level_matchers:
        if level_matcher.is_match(token_str):
            return level_matcher.log_level
    return UNKNOWN


METHOD_REGEX = re.compile(
    f'{TRACE_OPTIONS}|{DEBUG_OPTIONS}|{INFO_OPTIONS}|{WARN_OPTIONS}|{ERROR_OPTIONS}|{FATAL_OPTIONS}')

class SearchResult(Enum):
    NOT_FOUND = auto()
    FAILED = auto()
    IN_PROGRESS = auto()
    BUILT = auto


class LogSearchState(object):
    pass


class Searching(LogSearchState):
    def check(self, token):
        if isinstance(token, Word) and LOGGER_REGEX.fullmatch(str(token)):
            return SearchResult.IN_PROGRESS
        else:
            return SearchResult.NOT_FOUND

    def action(self, log_statement, token):
        log_statement.object_name = token
        return LoggerFound()


class LoggerFound(LogSearchState):
    def check(self, token):
        return SearchResult.IN_PROGRESS if token == '.' else SearchResult.FAILED

    def action(self, log_statement, token):
        return DotFound()


class DotFound(LogSearchState):
    def check(self, token):
        if isinstance(token, Word) and METHOD_REGEX.fullmatch(str(token)):
            return SearchResult.IN_PROGRESS
        else:
            return SearchResult.FAILED

    def action(self, log_statement: LogStatement, token):
        log_statement.method_name = token
        log_statement.level = get_log_level(str(token))
        return MethodFound()


class MethodFound(LogSearchState):
    def check(self, token):
        return SearchResult.IN_PROGRESS if token == '(' else SearchResult.FAILED

    def action(self, log_statement, token):
        return ClosingBracketFinder()


class ClosingBracketFinder(LogSearchState):
    LENGTH_LIMIT = 40

    def __init__(self):
        self.brackets_count = 1
        self.found = False
        self.current_length = 0

    def check(self, token):
        self.current_length += 1
        if self.current_length > ClosingBracketFinder.LENGTH_LIMIT:
            return SearchResult.FAILED
        if token == ')':
            if self.brackets_count == 1:
                # Found!
                self.found = True
            else:
                # there were some opening brackets after log statement start
                self.brackets_count -= 1
        elif token == '(':
            self.brackets_count += 1
        return SearchResult.IN_PROGRESS

    def action(self, log_statement, token):
        if not self.found:
            log_statement.add_to_log_content(token)
            return self
        else:
            return SemicolonFinder()


class SemicolonFinder(LogSearchState):
    def check(self, token):
        if token == ';':
            return SearchResult.BUILT
        elif isinstance(token, NewLine) or isinstance(token, Tab):
            # there can be some tabs or newlines before the semicolon
            return SearchResult.IN_PROGRESS
        else:  # something went wrong, no semicolon
            return SearchResult.FAILED

    def action(self, log_statement, token):
        log_statement.add_to_tokens_before_final_semicolon(token)
        return self


def mark(token_list, context):
    new_tokens = []
    suspected_log_tokens = []
    state = Searching()
    log_statement = LogStatement()
    for token in token_list:
        search_result = state.check(token)
        if search_result == SearchResult.NOT_FOUND:
            new_tokens.append(token)
        elif search_result == SearchResult.IN_PROGRESS:
            suspected_log_tokens.append(token)
            state = state.action(log_statement, token)
        elif search_result == SearchResult.FAILED:
            state = Searching()
            new_tokens.extend(suspected_log_tokens)  # in case 'log statement' was found,
            # but later wasn't marked as log statement
            suspected_log_tokens = []  # TODO come up with unit-tests that will fail without this line
            new_tokens.append(token)
        elif search_result == SearchResult.BUILT:
            new_tokens.append(log_statement)
            log_statement = LogStatement()
            suspected_log_tokens = []
            state = Searching()
        else:
            raise AssertionError()
    return new_tokens
