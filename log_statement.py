__author__ = 'hlib'


class LogStatement(object):
    def __init__(self, log_text_line, log_text, log_first_word, log_text_words, log_level, n_variables,
                 context, context_words, project, link):
        self.log_text_line = log_text_line
        self.log_text = log_text
        self.log_first_word = log_first_word
        self.log_text_words = log_text_words
        self.log_level = log_level
        self.n_variables = n_variables
        self.context = context
        self.context_words = context_words
        self.project = project
        self.link = link