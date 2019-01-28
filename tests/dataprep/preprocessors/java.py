import unittest

from logrec.dataprep.preprocessors.java import process_comments_and_str_literals
from logrec.dataprep.model.chars import OneLineCommentStart, NewLine, Quote, MultilineCommentStart, MultilineCommentEnd


# TODO write explanations with normal strings
from logrec.dataprep.model.containers import SplitContainer, StringLiteral, OneLineComment, MultilineComment
from logrec.dataprep.model.word import FullWord, SubWord


class JavaTest(unittest.TestCase):
    def test_process_comments_and_str_literals(self):
        '''
        Positive scenario

        <start>"//test_MyClass"
        //*/
        "/*!"
        /*
        /*
        <end>


        '''
        tokens = [Quote(),
                  OneLineCommentStart(),
                  SplitContainer([SubWord.of("test"),
                                  SubWord.of("_my"),
                                  SubWord.of("Class")]),
                  Quote(),
                  NewLine(),
                  OneLineCommentStart(),
                  MultilineCommentEnd(),
                  NewLine(),
                  Quote(),
                  MultilineCommentStart(),
                  FullWord.of("!"),
                  Quote(),
                  NewLine(),
                  MultilineCommentStart(),
                  NewLine(),
                  MultilineCommentEnd(),
                  NewLine(),
                  ]

        actual = process_comments_and_str_literals(tokens, {})

        expected = [StringLiteral([OneLineCommentStart(), SplitContainer([
            SubWord.of("test"),
            SubWord.of("_my"),
            SubWord.of("Class")],
        )]),
                    NewLine(),
                    OneLineComment([MultilineCommentEnd()]),
                    NewLine(),
                    StringLiteral([MultilineCommentStart(), FullWord.of("!")]),
                    NewLine(),
                    MultilineComment([NewLine()]),
                    NewLine()
                    ]

        self.assertEqual(expected, actual)

    def test_process_comments_and_str_literals_no_multiline_comment_start(self):
        tokens = [MultilineCommentEnd(), FullWord.of("a")]

        actual = process_comments_and_str_literals(tokens, {})

        expected = [MultilineCommentEnd(), FullWord.of("a")]

        self.assertEqual(expected, actual)

    def test_process_comments_and_str_literals_newline_after_open_quote(self):
        tokens = [Quote(), NewLine()]

        actual = process_comments_and_str_literals(tokens, {})

        expected = [Quote(), NewLine()]

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
