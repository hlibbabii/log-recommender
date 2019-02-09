import unittest

from logrec.dataprep.model.chars import OneLineCommentStart, NewLine, MultilineCommentEnd, MultilineCommentStart
# TODO write explanations with normal strings
from logrec.dataprep.model.containers import SplitContainer, StringLiteral, OneLineComment, MultilineComment
from logrec.dataprep.model.noneng import NonEng
from logrec.dataprep.model.word import Word, Underscore
from logrec.dataprep.preprocessors.noneng import mark


class NonengTest(unittest.TestCase):
    def test_mark_all_eng(self):
        '''
        All words are english. Nothing changed
        '''
        tokens = [StringLiteral([OneLineCommentStart(), SplitContainer([Word.from_("test"),
                                                                        Word.from_("my"),
                                                                        Word.from_("class")]
                                                                       )]),
                  NewLine(),
                  OneLineComment([MultilineCommentEnd(), SplitContainer.from_single_token("lifeisgood")]),
                  NewLine(),
                  StringLiteral([MultilineCommentStart(), SplitContainer.from_single_token("!")]),
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
                    Word.from_("A"),
                    Word.from_("Wirklich")
                ])
            ]),
            MultilineComment([
                SplitContainer.from_single_token('ц'),
                SplitContainer([
                    Word.from_("blanco"),
                    Underscore(),
                    Word.from_("english")
                ])
            ]),
            OneLineComment([
                SplitContainer([
                    Word.from_("DIESELBE"),
                    Word.from_("8")
                ])
            ])
        ]

        actual = mark(tokens, {})

        expected = [
            StringLiteral([
                SplitContainer([
                    Word.from_("A"),
                    NonEng(Word.from_("Wirklich"))
                ])
            ]),
            MultilineComment([
                SplitContainer([NonEng(Word.from_('ц'))]),
                SplitContainer([
                    # we have to call constructor manually here,
                    # case split container cannot set wordStart prefix
                    # when the first subword is wrapped in NonEng
                    NonEng(Word.from_("blanco")),
                    Underscore(),
                    Word.from_("english")
                ])
            ]),
            OneLineComment([
                SplitContainer([
                    # we have to call constructor manually here,
                    # case split container cannot set wordStart prefix
                    # when the first subword is wrapped in NonEng
                    NonEng(Word.from_("DIESELBE")),
                    Word.from_("8")
                ])
            ])
        ]
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
