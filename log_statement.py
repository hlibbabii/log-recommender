__author__ = 'hlib'


class LogStatement(object):
    def __init__(self, log_text, context, link):
        self.log_text = log_text
        self.context = context
        self.link = link