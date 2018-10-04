import unittest

from dataprep.preprocessors.model.chars import OneLineCommentStart, NewLine, MultilineCommentEnd, \
    MultilineCommentStart
from dataprep.preprocessors.model.general import ProcessableToken, NonEng
from dataprep.preprocessors.model.split import UnderscoreSplit, CamelCaseSplit, WithNumbersSplit
from dataprep.preprocessors.model.textcontainers import OneLineComment, StringLiteral, MultilineComment
# TODO write explanations with normal strings
from dataprep.preprocessors.noneng import mark


class NonengTest(unittest.TestCase):
    def test_mark_all_eng(self):
        '''
        All words are english. Nothing changed
        '''
        tokens = [StringLiteral([OneLineCommentStart(), UnderscoreSplit([ProcessableToken("test"),
                                                                         CamelCaseSplit([ProcessableToken("my"),
                                                                                         ProcessableToken("class")],
                                                                                        True)])]),
                  NewLine(),
                  OneLineComment([MultilineCommentEnd(), ProcessableToken("lifeisgood")]),
                  NewLine(),
                  StringLiteral([MultilineCommentStart(), ProcessableToken("!")]),
                  NewLine(),
                  MultilineComment([NewLine()]),
                  NewLine()
                  ]

        actual = mark(tokens, {})

        expected = [StringLiteral([OneLineCommentStart(), UnderscoreSplit([ProcessableToken("test"),
                                                                           CamelCaseSplit([ProcessableToken("my"),
                                                                                           ProcessableToken("class")],
                                                                                          True)])]),
                    NewLine(),
                    OneLineComment([MultilineCommentEnd(), ProcessableToken("lifeisgood")]),
                    NewLine(),
                    StringLiteral([MultilineCommentStart(), ProcessableToken("!")]),
                    NewLine(),
                    MultilineComment([NewLine()]),
                    NewLine()
                    ]

        self.assertEqual(actual, expected)

    def test_mark_with_noneng(self):
        tokens = [
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    ProcessableToken("wirklich")
                ], True)
            ]),
            MultilineComment([
                ProcessableToken('ц'),
                UnderscoreSplit([
                    ProcessableToken("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            OneLineComment([
                WithNumbersSplit([
                    ProcessableToken("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = mark(tokens, {})

        expected = [
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng("wirklich")
                ], True)
            ]),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
