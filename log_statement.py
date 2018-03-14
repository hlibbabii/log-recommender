__author__ = 'hlib'


class LogStatement(object):
    def __init__(self, log_text, log_level, n_variables, context, link):
        self.log_text = log_text
        self.log_level = log_level
        self.n_variables = n_variables
        self.context = context
        self.link = link