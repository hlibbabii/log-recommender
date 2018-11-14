import re
from enum import Enum, auto

from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
from logrec.dataprep.preprocessors.model.general import ProcessableToken
from logrec.dataprep.preprocessors.model.logging import LogStatement

LOGGER_REGEX = re.compile("[Ll]og|LOG|[Ll]ogger|LOGGER")
METHOD_REGEX = re.compile('[Tt]race|TRACE|[Dd]ebug|DEBUG|[Ii]nfo|INFO|[Ww]arn|WARN|[Ee]rror|ERROR|[Ff]atal'
                          '|FATAL|[Ff]inest|FINEST|[Ff]iner|FINER|[Ff]ine|FINE|[Cc]onfig|CONFIG'
                          '|[Ww]arning|WARNING|[Ss]evere|SEVERE')


class SearchResult(Enum):
    NOT_FOUND = auto()
    FAILED = auto()
    IN_PROGRESS = auto()
    BUILT = auto


class LogSearchState(object):
    pass


class Searching(LogSearchState):
    def check(self, token):
        if isinstance(token, ProcessableToken) and LOGGER_REGEX.fullmatch(token.get_val()):
            return SearchResult.IN_PROGRESS
        else:
            return SearchResult.NOT_FOUND

    def action(self, log_statement, token):
        log_statement.object_name = token.get_val()
        return LoggerFound()


class LoggerFound(LogSearchState):
    def check(self, token):
        return SearchResult.IN_PROGRESS if token == '.' else SearchResult.FAILED

    def action(self, log_statement, token):
        return DotFound()


class DotFound(LogSearchState):
    def check(self, token):
        if isinstance(token, ProcessableToken) and METHOD_REGEX.fullmatch(token.get_val()):
            return SearchResult.IN_PROGRESS
        else:
            return SearchResult.FAILED

    def action(self, log_statement, token):
        log_statement.method_name = token.get_val()
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
