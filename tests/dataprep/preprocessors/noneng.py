import unittest

from logrec.dataprep.model.chars import OneLineCommentStart, NewLine, MultilineCommentEnd, \
    MultilineCommentStart
# TODO write explanations with normal strings
from logrec.dataprep.model.containers import SplitContainer, StringLiteral, OneLineComment, \
    MultilineComment
from logrec.dataprep.model.noneng import NonEng, NonEngSubWord, NonEngFullWord
from logrec.dataprep.model.word import Word, FullWord, SubWord, Capitalization, WordStart
from logrec.dataprep.preprocessors.noneng import mark


class NonengTest(unittest.TestCase):
    def test_mark_all_eng(self):
        '''
        All words are english. Nothing changed
        '''
        tokens = [StringLiteral([OneLineCommentStart(), SplitContainer([SubWord.of("test"),
                                                                        SubWord.of("my"),
                                                                        SubWord.of("class")]
                                                                       )]),
                  NewLine(),
                  OneLineComment([MultilineCommentEnd(), FullWord.of("lifeisgood")]),
                  NewLine(),
                  StringLiteral([MultilineCommentStart(), FullWord.of("!")]),
                  NewLine(),
                  MultilineComment([NewLine()]),
                  NewLine()
                  ]

        actual = mark(tokens, {})

        self.assertEqual(actual, tokens)

    def test_mark_with_noneng(self):
        tokens = [
            StringLiteral([
                SplitContainer([
                    SubWord.of("A"),
                    SubWord.of("Wirklich")
                ])
            ]),
            MultilineComment([
                FullWord.of('ц'),
                SplitContainer([
                    SubWord.of("blanco"),
                    SubWord.of("_english")
                ])
            ]),
            OneLineComment([
                SplitContainer([
                    SubWord.of("DIESELBE"),
                    SubWord.of("8")
                ])
            ])
        ]

        actual = mark(tokens, {})

        expected = [
            StringLiteral([
                SplitContainer([
                    SubWord.of("A"),
                    NonEngSubWord(SubWord.of("Wirklich"))
                ])
            ]),
            MultilineComment([
                NonEngFullWord(FullWord.of('ц')),
                SplitContainer([
                    # we have to call constructor manually here,
                    # case split container cannot set wordStart prefix
                    # when the first subword is wrapped in NonEng
                    NonEngSubWord(SubWord("blanco", Capitalization.NONE, WordStart())),
                    SubWord.of("_english")
                ])
            ]),
            OneLineComment([
                SplitContainer([
                    # we have to call constructor manually here,
                    # case split container cannot set wordStart prefix
                    # when the first subword is wrapped in NonEng
                    NonEngSubWord(SubWord("dieselbe", Capitalization.ALL, WordStart())),
                    SubWord.of("8")
                ])
            ])
        ]
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
