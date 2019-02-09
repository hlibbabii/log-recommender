import unittest

from logrec.dataprep.model.word import Word, Underscore
from logrec.dataprep.preprocessors import logs
from logrec.dataprep.model.chars import NewLine, Tab
from logrec.dataprep.model.containers import SplitContainer, StringLiteral
from logrec.dataprep.model.logging import LogStatement, INFO, DEBUG, FATAL, TRACE
from logrec.dataprep.model.numeric import HexStart, Number, L


class MarkLogTest(unittest.TestCase):
    def test_no_logs(self):
        input = [NewLine(),
                 SplitContainer.from_single_token('long'),
                 '[',
                 ']',
                 SplitContainer([Word.from_('lovely'), Underscore(), Word.from_('longs')]),
                 '=',
                 '{',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L
                 ()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_simple_log(self):
        input = [NewLine(),
                 SplitContainer.from_single_token('log'),
                 '.', SplitContainer.from_single_token('info'),
                 '(',
                 StringLiteral([SplitContainer.from_single_token("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement(SplitContainer.from_single_token('log'),
                                 SplitContainer.from_single_token('info'), INFO,
                                 [StringLiteral([SplitContainer.from_single_token("Hi")])]),
                    Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        self.assertEqual(expected, actual)

    def test_tabs_and_newlines_before_semicolon(self):
        input = [NewLine(),
                 SplitContainer.from_single_token('log'),
                 '.', SplitContainer.from_single_token('d'),
                 '(',
                 StringLiteral([SplitContainer.from_single_token("Hi")]),
                 ')', NewLine(), NewLine(), Tab(), Tab(), ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement(SplitContainer.from_single_token('log'),
                                 SplitContainer.from_single_token('d'), DEBUG,
                                 [StringLiteral([SplitContainer.from_single_token("Hi")])],
                                 [NewLine(), NewLine(), Tab(), Tab()]),
                    Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        self.assertEqual(expected, actual)

    def test_no_semicolon(self):
        input = [NewLine(),
                 SplitContainer.from_single_token('log'),
                 '.', SplitContainer.from_single_token('info'),
                 '(',
                 StringLiteral([SplitContainer.from_single_token("Hi")]),
                 ')',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_no_dot(self):
        input = [NewLine(),
                 SplitContainer.from_single_token('log'),
                 SplitContainer.from_single_token('infooooo'),
                 '(',
                 StringLiteral([SplitContainer.from_single_token("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_no_dot_twice(self):
        input = [NewLine(),
                 SplitContainer.from_single_token('log'),
                 SplitContainer.from_single_token('log'),
                 SplitContainer.from_single_token('infooooo'),
                 '(',
                 StringLiteral([SplitContainer.from_single_token("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_wrong_method_name(self):
        input = [NewLine(),
                 SplitContainer.from_single_token('log'),
                 '.', SplitContainer.from_single_token('infooooo'),
                 '(',
                 StringLiteral([SplitContainer.from_single_token("Hi")]),
                 ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        self.assertEqual(input, actual)

    def test_spare_brackets(self):
        input = [NewLine(),
                 SplitContainer.from_single_token('log'),
                 '.', SplitContainer.from_single_token('logI'),
                 '(', '(',
                 StringLiteral([SplitContainer.from_single_token("Hi")]),
                 ')', '*', Number(['2']), ')', ';',
                 Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement(SplitContainer.from_single_token('log'), SplitContainer.from_single_token('logI'),
                                 INFO,
                                 ['(', StringLiteral([SplitContainer.from_single_token("Hi")]),
                                                 ')', '*', Number(['2'])]),
                    Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()])]

        self.assertEqual(expected, actual)

    def test_2_logs(self):
        input = [NewLine(),
                 SplitContainer.from_single_token('log'), '.', SplitContainer.from_single_token('t'),
                 '(', StringLiteral([SplitContainer.from_single_token("Hi")]), ')', ';',
                 NewLine(),
                 SplitContainer.from_single_token('Logger'), '.', SplitContainer.from_single_token('SEVERE'),
                 '(', StringLiteral([SplitContainer.from_single_token("Hi")]), ')', ';', ]

        actual = logs.mark(input, None)

        expected = [NewLine(),
                    LogStatement(SplitContainer.from_single_token('log'),
                                 SplitContainer.from_single_token('t'), TRACE,
                                 [StringLiteral([SplitContainer.from_single_token("Hi")])]),
                    NewLine(), LogStatement(SplitContainer.from_single_token('Logger'),
                                            SplitContainer.from_single_token('SEVERE'), FATAL,
                                            [StringLiteral([SplitContainer.from_single_token("Hi")])])]

        self.assertEqual(expected, actual)

    def test_content_length_over_limit(self):
        input = [NewLine(),
                 SplitContainer.from_single_token('log'),
                 '.', SplitContainer.from_single_token('info'),
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
