import unittest

from logrec.dataprep.preprocessors import loggable
from logrec.dataprep.model.chars import NewLine
from logrec.dataprep.model.containers import MultilineComment, StringLiteral, SplitContainer
from logrec.dataprep.model.logging import LoggableBlock


class MarkLogTest(unittest.TestCase):
    def test_nested_data_class(self):
        input = ['{', '}',
                 MultilineComment([SplitContainer.from_single_token("class")]),
                 SplitContainer.from_single_token('import'),
                 SplitContainer.from_single_token("a"),
                 NewLine(),
                 SplitContainer.from_single_token('class'),
                 SplitContainer.from_single_token('A'), '{',
                 SplitContainer.from_single_token('void'),
                 SplitContainer.from_single_token('print1'), '(', ')', '{',
                 SplitContainer.from_single_token('if'), '(',
                 SplitContainer.from_single_token('True'), ')', '{', '}',
            '}',
                 SplitContainer.from_single_token('static'),
                 SplitContainer.from_single_token('private'),
                 SplitContainer.from_single_token('class'),
                 SplitContainer.from_single_token('B'),
                 SplitContainer.from_single_token('extends'),
                 SplitContainer.from_single_token('D'), '{',
                 SplitContainer.from_single_token('private'),
                 SplitContainer.from_single_token('String'),
                 SplitContainer.from_single_token('b'), ';',
                 SplitContainer.from_single_token('B'), '(', ')', '{', '}',
                 SplitContainer.from_single_token('static'), '{',
                 SplitContainer.from_single_token('c'), '=',
                 StringLiteral([SplitContainer.from_single_token('class')]), '.',
                 SplitContainer.from_single_token('class'), '}',
            '}',
                 SplitContainer.from_single_token('void'),
                 SplitContainer.from_single_token('print'), '(', ')', '{',
                 SplitContainer.from_single_token('if'), '(',
                 SplitContainer.from_single_token('True'), ')', '{', '}',
            '}',
                 SplitContainer.from_single_token('int'),
                 SplitContainer.from_single_token('a'), ';',
            '}',
                 ]

        actual = loggable.mark(input, None)

        expected = ['{', '}',
                    MultilineComment([SplitContainer.from_single_token("class")]),
                    SplitContainer.from_single_token('import'), SplitContainer.from_single_token("a"),
                    NewLine(),
                    SplitContainer.from_single_token('class'), SplitContainer.from_single_token('A'), '{',
                    SplitContainer.from_single_token('void'), SplitContainer.from_single_token('print1'), '(', ')',
                    LoggableBlock(['{',
                                   SplitContainer.from_single_token('if'), '(',
                                   SplitContainer.from_single_token('True'), ')', '{', '}',
                                                                                 '}']),
                    SplitContainer.from_single_token('static'),
                    SplitContainer.from_single_token('private'),
                    SplitContainer.from_single_token('class'),
                    SplitContainer.from_single_token('B'),
                    SplitContainer.from_single_token('extends'),
                    SplitContainer.from_single_token('D'), '{',
                    SplitContainer.from_single_token('private'),
                    SplitContainer.from_single_token('String'),
                    SplitContainer.from_single_token('b'), ';',
                    SplitContainer.from_single_token('B'), '(', ')', LoggableBlock(['{', '}']),
                    SplitContainer.from_single_token('static'),
                    LoggableBlock(
                        ['{', SplitContainer.from_single_token('c'), '=',
                         StringLiteral([SplitContainer.from_single_token('class')]), '.',
                         SplitContainer.from_single_token('class'), '}']),
                    '}',
                    SplitContainer.from_single_token('void'), SplitContainer.from_single_token('print'), '(', ')',
                    LoggableBlock(
                        ['{', SplitContainer.from_single_token('if'), '(', SplitContainer.from_single_token('True'),
                         ')', '{', '}', '}']),
                    SplitContainer.from_single_token('int'), SplitContainer.from_single_token('a'), ';',
                    '}'
                    ]

        self.assertEqual(expected, actual)

    def test_class_closing_bracket(self):
        input = [SplitContainer.from_single_token('class'), '}']

        actual = loggable.mark(input, None)

    def test_class_class(self):
        input = [SplitContainer.from_single_token('class'),
                 SplitContainer.from_single_token('A'),
                 SplitContainer.from_single_token('class')]

        actual = loggable.mark(input, None)

    def test_closing_bracket(self):
        input = ['}']

        actual = loggable.mark(input, None)


if __name__ == '__main__':
    unittest.main()
