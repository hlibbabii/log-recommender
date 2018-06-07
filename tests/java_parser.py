import unittest

from deepdiff import DeepDiff

from log_recommender.java_parser import JavaParser


class JavaParserTest():
    def test_strip_off_multiline_comments(self):
        context = ["a", "*/", "1", "/*", "wer", "=", "3", "*/", "8", "/*", "print"]

        actual = JavaParser().strip_off_multiline_comments(context)

        expected = ["<comment>", "1", "<comment>", "8", "<comment>"]

        print(DeepDiff(expected, actual))

    def test_strip_off_string_literal0(self):
        context = ['"', '4', '"']

        actual = JavaParser().strip_off_string_literals(context)

        expected = ["<string_literal>"]

        print(DeepDiff(expected, actual))

    def test_strip_off_string_literal(self):
        context = ['"', '\\', '"', '"']

        actual = JavaParser().strip_off_string_literals(context)

        expected = ["<string_literal>"]

        print(DeepDiff(expected, actual))

    def test_strip_off_string_literal2(self):
        context = ['"', '\\', '\\', '"', '"', '"']

        actual = JavaParser().strip_off_string_literals(context)

        expected = ["<string_literal>", "<string_literal>"]

        print(DeepDiff(expected, actual))

    def test_strip_off_string_literal2(self):
        context = ['\t1', 'try', '{', '\n', '\t2', 'selendroidStandaloneDriver', '.', 'addToAppsStore', '(', 'file', ')', ';',
         '\n', '\t2', 'log', '.', 'info', '(', '"', 'File', 'added', 'to', 'app', 'store', ':', '\\', 'n', '\\', 't',
         '<string_literal>']

        actual = JavaParser().strip_off_string_literals(context)

        expected = ['\t1', 'try', '{', '\n', '\t2', 'selendroidStandaloneDriver', '.', 'addToAppsStore', '(', 'file', ')', ';',
         '\n', '\t2', 'log', '.', 'info', '(', '"', 'File', 'added', 'to', 'app', 'store', ':', '\\', 'n', '\\', 't',
         '<string_literal>']

        print(DeepDiff(expected, actual))


if __name__ == '__main__':
   JavaParserTest().test_strip_off_multiline_comments()
   JavaParserTest().test_strip_off_string_literal0()
   JavaParserTest().test_strip_off_string_literal()
   JavaParserTest().test_strip_off_string_literal2()