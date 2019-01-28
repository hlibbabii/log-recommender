import unittest

from logrec.dataprep.preprocessors import loggable
from logrec.dataprep.model.chars import NewLine
from logrec.dataprep.model.containers import MultilineComment, StringLiteral
from logrec.dataprep.model.logging import LoggableBlock
from logrec.dataprep.model.word import FullWord


class MarkLogTest(unittest.TestCase):
    def test_nested_data_class(self):
        input = ['{', '}',
                 MultilineComment([FullWord.of("class")]),
                 FullWord.of('import'), FullWord.of("a"),
                 NewLine(),
                 FullWord.of('class'), FullWord.of('A'), '{',
                 FullWord.of('void'), FullWord.of('print1'), '(', ')', '{',
                 FullWord.of('if'), '(', FullWord.of('True'), ')', '{', '}',
            '}',
                 FullWord.of('static'), FullWord.of('private'),
                 FullWord.of('class'), FullWord.of('B'), FullWord.of('extends'), FullWord.of('D'), '{',
                 FullWord.of('private'), FullWord.of('String'), FullWord.of('b'), ';',
                 FullWord.of('B'), '(', ')', '{', '}',
                 FullWord.of('static'), '{', FullWord.of('c'), '=', StringLiteral([FullWord('class')]), '.',
                 FullWord.of('class'), '}',
            '}',
                 FullWord.of('void'), FullWord.of('print'), '(', ')', '{',
                 FullWord.of('if'), '(', FullWord.of('True'), ')', '{', '}',
            '}',
                 FullWord.of('int'), FullWord.of('a'), ';',
            '}',
                 ]

        actual = loggable.mark(input, None)

        expected = ['{', '}',
                    MultilineComment([FullWord.of("class")]),
                    FullWord.of('import'), FullWord.of("a"),
                    NewLine(),
                    FullWord.of('class'), FullWord.of('A'), '{',
                    FullWord.of('void'), FullWord.of('print1'), '(', ')', LoggableBlock(['{',
                                                                                 FullWord.of('if'), '(',
                                                                                 FullWord.of('True'), ')', '{', '}',
                                                                                 '}']),
                    FullWord.of('static'), FullWord.of('private'),
                    FullWord.of('class'), FullWord.of('B'), FullWord.of('extends'), FullWord.of('D'), '{',
                    FullWord.of('private'), FullWord.of('String'), FullWord.of('b'), ';',
                    FullWord.of('B'), '(', ')', LoggableBlock(['{', '}']),
                    FullWord.of('static'),
                    LoggableBlock(
                ['{', FullWord.of('c'), '=', StringLiteral([FullWord('class')]), '.', FullWord.of('class'), '}']),
                    '}',
                    FullWord.of('void'), FullWord.of('print'), '(', ')',
                    LoggableBlock(['{', FullWord.of('if'), '(', FullWord.of('True'), ')', '{', '}', '}']),
                    FullWord.of('int'), FullWord.of('a'), ';',
                    '}'
                    ]

        self.assertEqual(expected, actual)

    def test_class_closing_bracket(self):
        input = [FullWord.of('class'), '}']

        actual = loggable.mark(input, None)

    def test_class_class(self):
        input = [FullWord.of('class'), FullWord.of('A'), FullWord.of('class')]

        actual = loggable.mark(input, None)

    def test_closing_bracket(self):
        input = ['}']

        actual = loggable.mark(input, None)


if __name__ == '__main__':
    unittest.main()
