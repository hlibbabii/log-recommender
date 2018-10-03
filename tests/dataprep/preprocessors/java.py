import unittest

from dataprep.preprocessors.java import process_comments_and_str_literals
from dataprep.preprocessors.model.chars import OneLineCommentStart, NewLine, Quote, MultilineCommentEnd, \
    MultilineCommentStart
from dataprep.preprocessors.model.general import ProcessableToken
from dataprep.preprocessors.model.split import UnderscoreSplit, CamelCaseSplit
from dataprep.preprocessors.model.textcontainers import OneLineComment, StringLiteral, MultilineComment


# TODO write explanations with normal strings
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
                  UnderscoreSplit([ProcessableToken("test"),
                                   CamelCaseSplit([ProcessableToken("my"),
                                                   ProcessableToken("class")], True)]),
                  Quote(),
                  NewLine(),
                  OneLineCommentStart(),
                  MultilineCommentEnd(),
                  NewLine(),
                  Quote(),
                  MultilineCommentStart(),
                  ProcessableToken("!"),
                  Quote(),
                  NewLine(),
                  MultilineCommentStart(),
                  NewLine(),
                  MultilineCommentEnd(),
                  NewLine(),
                  ]

        actual = process_comments_and_str_literals(tokens, {})

        expected = [StringLiteral([OneLineCommentStart(), UnderscoreSplit([ProcessableToken("test"),
                                                                           CamelCaseSplit([ProcessableToken("my"),
                                                                                           ProcessableToken("class")],
                                                                                          True)])]),
                    NewLine(),
                    OneLineComment([MultilineCommentEnd()]),
                    NewLine(),
                    StringLiteral([MultilineCommentStart(), ProcessableToken("!")]),
                    NewLine(),
                    MultilineComment([NewLine()]),
                    NewLine()
                    ]

        self.assertEqual(actual, expected)

    def test_process_comments_and_str_literals_no_multiline_comment_start(self):
        tokens = [MultilineCommentEnd(), ProcessableToken("a")]

        actual = process_comments_and_str_literals(tokens, {})

        expected = [MultilineCommentEnd(), ProcessableToken("a")]

        self.assertEqual(actual, expected)

    def test_process_comments_and_str_literals_newline_after_open_quote(self):
        tokens = [Quote(), NewLine()]

        actual = process_comments_and_str_literals(tokens, {})

        expected = [Quote(), NewLine()]

        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
