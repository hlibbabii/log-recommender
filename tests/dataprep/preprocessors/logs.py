import unittest

from logrec.dataprep.preprocessors import logs
from logrec.dataprep.model.chars import NewLine, Tab
from logrec.dataprep.model.containers import SplitContainer, StringLiteral
from logrec.dataprep.model.logging import LogStatement, INFO, DEBUG, FATAL, TRACE
from logrec.dataprep.model.numeric import HexStart, Number, L
from logrec.dataprep.model.word import Word, FullWord


class MarkLogTest(unittest.TestCase):
    def test_no_logs(self):
        input = [NewLine(),
                 FullWord.of('long'),
                 '[',
                 ']',
                 SplitContainer([FullWord.of('lovely'), FullWord.of('_longs')]),
                 '=',
                 '{',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L
                 ()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_simple_log(self):
        input = [NewLine(),
                 FullWord.of('log'),
                 '.', FullWord.of('info'),
                 '(',
                 StringLiteral([FullWord.of("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement(FullWord.of('log'), FullWord.of('info'), INFO, [StringLiteral([FullWord.of("Hi")])]),
                    Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        self.assertEqual(expected, actual)

    def test_tabs_and_newlines_before_semicolon(self):
        input = [NewLine(),
                 FullWord.of('log'),
                 '.', FullWord.of('d'),
                 '(',
                 StringLiteral([FullWord.of("Hi")]),
                 ')', NewLine(), NewLine(), Tab(), Tab(), ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement(FullWord.of('log'), FullWord.of('d'), DEBUG, [StringLiteral([FullWord.of("Hi")])],
                                 [NewLine(), NewLine(), Tab(), Tab()]),
                    Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        self.assertEqual(expected, actual)

    def test_no_semicolon(self):
        input = [NewLine(),
                 FullWord.of('log'),
                 '.', FullWord.of('info'),
                 '(',
                 StringLiteral([FullWord.of("Hi")]),
                 ')',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_no_dot(self):
        input = [NewLine(),
                 FullWord.of('log'),
                 FullWord.of('infooooo'),
                 '(',
                 StringLiteral([FullWord.of("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_no_dot_twice(self):
        input = [NewLine(),
                 FullWord.of('log'), FullWord.of('log'),
                 FullWord.of('infooooo'),
                 '(',
                 StringLiteral([FullWord.of("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_wrong_method_name(self):
        input = [NewLine(),
                 FullWord.of('log'),
                 '.', FullWord.of('infooooo'),
                 '(',
                 StringLiteral([FullWord.of("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_spare_brackets(self):
        input = [NewLine(),
                 FullWord.of('log'),
                 '.', FullWord.of('logI'),
                 '(', '(',
                 StringLiteral([FullWord.of("Hi")]),
                 ')', '*', Number(['2']), ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement(FullWord.of('log'), FullWord.of('logI'), INFO,
                                 ['(', StringLiteral([FullWord.of("Hi")]),
                                                 ')', '*', Number(['2'])]),
                    Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        self.assertEqual(expected, actual)

    def test_2_logs(self):
        input = [NewLine(),
                 FullWord.of('log'), '.', FullWord.of('t'),
                 '(', StringLiteral([FullWord.of("Hi")]), ')', ';',
                 NewLine(),
                 FullWord.of('Logger'), '.', FullWord.of('SEVERE'),
                 '(', StringLiteral([FullWord.of("Hi")]), ')', ';', ]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement(FullWord.of('log'), FullWord.of('t'), TRACE, [StringLiteral([FullWord.of("Hi")])]),
                    NewLine(), LogStatement(FullWord.of('Logger'), FullWord.of('SEVERE'), FATAL,
                                            [StringLiteral([FullWord.of("Hi")])])]

        self.assertEqual(expected, actual)

    def test_content_length_over_limit(self):
        input = [NewLine(),
                 FullWord.of('log'),
                 '.', FullWord.of('info'),
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
