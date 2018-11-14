import unittest

from logrec.dataprep.preprocessors import logs
from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
from logrec.dataprep.preprocessors.model.general import ProcessableToken
from logrec.dataprep.preprocessors.model.logging import LogStatement
from logrec.dataprep.preprocessors.model.numeric import HexStart, Number, L
from logrec.dataprep.preprocessors.model.split import UnderscoreSplit
from logrec.dataprep.preprocessors.model.textcontainers import StringLiteral


class MarkLogTest(unittest.TestCase):
    def test_no_logs(self):
        input = [NewLine(),
                 ProcessableToken('long'),
                 '[',
                 ']',
                 UnderscoreSplit([ProcessableToken('lovely'), ProcessableToken('longs')]),
                 '=',
                 '{',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L
                 ()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_simple_log(self):
        input = [NewLine(),
                 ProcessableToken('log'),
                 '.', ProcessableToken('info'),
                 '(',
                 StringLiteral([ProcessableToken("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement('log', 'info', [StringLiteral([ProcessableToken("Hi")])]),
                    Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        self.assertEqual(expected, actual)

    def test_tabs_and_newlines_before_semicolon(self):
        input = [NewLine(),
                 ProcessableToken('log'),
                 '.', ProcessableToken('info'),
                 '(',
                 StringLiteral([ProcessableToken("Hi")]),
                 ')', NewLine(), NewLine(), Tab(), Tab(), ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement('log', 'info', [StringLiteral([ProcessableToken("Hi")])],
                                 [NewLine(), NewLine(), Tab(), Tab()]),
                    Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        self.assertEqual(expected, actual)

    def test_no_semicolon(self):
        input = [NewLine(),
                 ProcessableToken('log'),
                 '.', ProcessableToken('info'),
                 '(',
                 StringLiteral([ProcessableToken("Hi")]),
                 ')',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_no_dot(self):
        input = [NewLine(),
                 ProcessableToken('log'),
                 ProcessableToken('infooooo'),
                 '(',
                 StringLiteral([ProcessableToken("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_no_dot_twice(self):
        input = [NewLine(),
                 ProcessableToken('log'), ProcessableToken('log'),
                 ProcessableToken('infooooo'),
                 '(',
                 StringLiteral([ProcessableToken("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_wrong_method_name(self):
        input = [NewLine(),
                 ProcessableToken('log'),
                 '.', ProcessableToken('infooooo'),
                 '(',
                 StringLiteral([ProcessableToken("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_spare_brackets(self):
        input = [NewLine(),
                 ProcessableToken('log'),
                 '.', ProcessableToken('info'),
                 '(', '(',
                 StringLiteral([ProcessableToken("Hi")]),
                 ')', '*', Number(2), ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement('log', 'info', ['(', StringLiteral([ProcessableToken("Hi")]),
                                                 ')', '*', Number(2)]),
                    Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        self.assertEqual(expected, actual)

    def test_2_logs(self):
        input = [NewLine(),
                 ProcessableToken('log'), '.', ProcessableToken('info'),
                 '(', StringLiteral([ProcessableToken("Hi")]), ')', ';',
                 NewLine(),
                 ProcessableToken('logger'), '.', ProcessableToken('SEVERE'),
                 '(', StringLiteral([ProcessableToken("Hi")]), ')', ';', ]

        actual = logs.mark(input, None)

        expected = [NewLine(), LogStatement('log', 'info', [StringLiteral([ProcessableToken("Hi")])]),
                    NewLine(), LogStatement('logger', 'SEVERE', [StringLiteral([ProcessableToken("Hi")])])]

        self.assertEqual(expected, actual)

    def test_content_length_over_limit(self):
        input = [NewLine(),
                 ProcessableToken('log'),
                 '.', ProcessableToken('info'),
                 '(', '(', '(', '(', '(', '(', '(', '(',
                 '(', '(', '(', '(', '(', '(', '(', '(',
                 '(', '(', '(', '(', '(', '(', '(', '(',
                 '(', '(', '(', '(', '(', '(', '(', '(',
                 '1', '*', '3', ')', ')', ')', ')', ')', ')', ')', ')',
                 ')', ')', ')', ')', ')', ')', ')', ')'
                                                    ')', ')', ')', ')', ')', ')', ')', ')'
                                                                                       ')', ')', ')', ')', ')', ')',
                 ')', ')'
                      ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)


if __name__ == '__main__':
    unittest.main()
