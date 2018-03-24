__author__ = 'hlib'


class LogStatement(object):
    def __init__(self, log_text_line, log_text, log_first_word, first_word_cathegory, log_text_words, log_level, n_variables,
                 context, context_words, link):
        self.log_text_line = log_text_line
        self.log_text = log_text
        self.log_first_word = log_first_word
        self.first_word_cathegory = first_word_cathegory
        self.log_text_words = log_text_words
        self.log_level = log_level
        self.n_variables = n_variables
        self.context = context
        self.context_words = context_words
        self.link = link