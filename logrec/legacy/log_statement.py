import sys

from logrec.dataprep.preprocessors import apply_preprocessors
from logrec.dataprep.preprocessors.general import replace_4whitespaces_with_tabs, spl_verbose, from_list

__author__ = 'hlib'

class LogContext(object):
    def __init__(self, context_before, context_after):
        self.context_before = context_before
        self.context_after = context_after
        # self.context_words = preprocess_context(self.context_before + self.context_after)
        self.context_words = apply_preprocessors(from_list(self.context_before), [
            replace_4whitespaces_with_tabs,
            spl_verbose,
            lambda context_line: [item.lower() for identifier in context_line for item in camel_case_split(identifier)]
        ])

    def get_context_words(self, n_lines_to_consider):
        return [w for w_list in self.context_words[-n_lines_to_consider:] for w in w_list]

    def get_marked_up_context(self, interesting_words):
        BEFORE = "[red]##"
        AFTER = "##"
        locations=[]
        concat_context_before = "".join(self.context_before)
        lowercase_context = concat_context_before.lower()
        start_position = 0
        continue_search_from_index = 0
        symbols_at_least_skipped = 0
        merged_context_words = self.get_context_words(sys.maxsize)
        for word in interesting_words:
            if word == '':
                raise AssertionError("word is empty in " + interesting_words)
            next_word_list_index = continue_search_from_index + merged_context_words[continue_search_from_index:].index(word)
            symbols_at_least_skipped = start_position + \
                        sum(map(lambda x: len(x), merged_context_words[continue_search_from_index:next_word_list_index]))
            continue_search_from_index = next_word_list_index + 1
            found_start = lowercase_context.find(word, max(start_position, symbols_at_least_skipped))
            if found_start == -1 or next_word_list_index == -1:
                raise AssertionError(word + " not found in:\n" + concat_context_before + "")
            locations.append((concat_context_before[start_position:found_start],
                             concat_context_before[found_start: found_start + len(word)]))
            start_position = found_start + len(word)
        last_location = concat_context_before[start_position:]
        marked_up_string = "[literal,subs=\"quotes\"]\n"
        for location in locations:
            # marked_up_string += RAW
            marked_up_string += location[0]
            # marked_up_string += RAW
            marked_up_string += BEFORE
            # marked_up_string += RAW
            marked_up_string += location[1]
            # marked_up_string += RAW
            marked_up_string += AFTER
        marked_up_string += last_location
        return marked_up_string


log_count = 0


class LogStatement(object):

    log_count = 0

    def __init__(self, text_line, text_words, level, n_variables,
                 context_before, context_after, project, link):
        self.text_line = text_line
        self.text_words = text_words
        self.level = level
        self.n_variables = n_variables
        self.context = LogContext(context_before, context_after)
        self.project = project
        self.link = link
        self.id = self.__generate_id__()

    def neg_or_pos(self):
        return 'pos' if self.level in ['trace', 'debug', 'info'] else 'neg'

    def __generate_id__(self):
        id = self.project[:6] + "_" + str(LogStatement.log_count)
        LogStatement.log_count += 1
        return id

    def get_first_words(self, how_many):
        first_words = self.text_words[:how_many]
        first_words.extend([''] * (how_many - len(first_words)))
        return first_words


    def get_first_word(self):
        return self.text_words[0] if len(self.text_words) > 0 else ""

    def get_marked_up_context(self, interesting_words):
        return self.context.get_marked_up_context(interesting_words)

    def get_context_words(self, n_lines_to_consider):
        return self.context.get_context_words(n_lines_to_consider)