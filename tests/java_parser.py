import unittest

from deepdiff import DeepDiff

from log_recommender.java_parser import JavaParser


class JavaParserTest(unittest.TestCase):
    def test_find_not_escaped_double_quote_trivial(self):
        context = ['4', '"']

        actual = JavaParser().find_not_escaped_double_quote(context)

        expected = 1

        self.assertEqual(expected, actual)

    def test_find_not_escaped_double_quote_trivial_none(self):
        context = ['4']

        actual = JavaParser().find_not_escaped_double_quote(context)

        expected = None

        self.assertEqual(expected, actual)

    def test_find_not_escaped_double_quote_none(self):
        context = ['\\', '"','4']

        actual = JavaParser().find_not_escaped_double_quote(context)

        expected = None

        self.assertEqual(expected, actual)

    def test_find_not_escaped_double_quote_two_slashes(self):
        context = ['\\', '\\', '"', '4']

        actual = JavaParser().find_not_escaped_double_quote(context)

        expected = 2

        self.assertEqual(expected, actual)

    def test_find_not_escaped_double_quote_multiple_escaped_quotes(self):
        context = ['\\', '"', '\\', '\\', '"', '4ed']

        actual = JavaParser().find_not_escaped_double_quote(context)

        expected = 4

        self.assertEqual(expected, actual)

    def test_find_not_escaped_long_seq_before_quote(self):
        context = ['dededede', 'erdfsf', 'eee', 'de', '\\', '"', '4ed']

        actual = JavaParser().find_not_escaped_double_quote(context)

        expected = None

        self.assertEqual(expected, actual)

    def test_find_not_escaped_double_quote_7_slashes(self):
        context = ['\\', '"', '\\', '\\', '\\', '\\', '\\', '\\', '\\', '"', '4']

        actual = JavaParser().find_not_escaped_double_quote(context)

        expected = None

        self.assertEqual(expected, actual)

    def test_strip_off_multiline_comments(self):
        context = ["a", "*/", "1", "/*", "wer", "=", "3", "*/", "8", "/*", "print"]

        actual = JavaParser().strip_off_multiline_comments(context)

        expected = ["<comment>", "1", "<comment>", "8", "<comment>"]

        self.assertEqual(DeepDiff(expected, actual), {})

    def test_strip_off_string_literal0(self):
        context = ['"', '4', '"']

        actual = JavaParser().strip_off_string_literals(context)

        expected = ["<string_literal>"]

        self.assertEqual(DeepDiff(expected, actual), {})

    def test_strip_off_string_literal(self):
        context = ['"', '\\', '"', '"']

        actual = JavaParser().strip_off_string_literals(context)

        expected = ["<string_literal>"]

        self.assertEqual(DeepDiff(expected, actual), {})

    def test_strip_off_string_literal2(self):
        context = ['"', '\\', '\\', '"', '"', '"']

        actual = JavaParser().strip_off_string_literals(context)

        expected = ["<string_literal>", "<string_literal>"]

        self.assertEqual(DeepDiff(expected, actual), {})

    def test_strip_off_string_literal3(self):
        context = ['\t1', 'try', '{', '\n', '\t2', 'selendroidStandaloneDriver', '.', 'addToAppsStore', '(', 'file', ')', ';',
         '\n', '\t2', 'log', '.', 'info', '(', '"', 'File', 'added', 'to', 'app', 'store', ':', '\\', 'n', '\\', 't', '"']

        actual = JavaParser().strip_off_string_literals(context)

        expected = ['\t1', 'try', '{', '\n', '\t2', 'selendroidStandaloneDriver', '.', 'addToAppsStore', '(', 'file', ')', ';',
         '\n', '\t2', 'log', '.', 'info', '(', '<string_literal>']

        self.assertEqual(DeepDiff(expected, actual), {})


if __name__ == '__main__':
    unittest.main()
