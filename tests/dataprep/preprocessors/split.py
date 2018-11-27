import unittest

from logrec.dataprep.preprocessors.model.containers import StringLiteral, SplitContainer
from logrec.dataprep.preprocessors.model.word import Word, SubWord, ParseableToken
from logrec.dataprep.preprocessors.split import simple_split


class SplitTest(unittest.TestCase):

    def test_with_numbers_split(self):
        token = [StringLiteral([":", ParseableToken("_test_my123GmyClass_")])]
        actual = simple_split(token, {})

        expected = [StringLiteral([":", SplitContainer([SubWord.of("_test"),
                                                        SubWord.of("_my"),
                                                        SubWord.of("123"),
                                                        SubWord.of("Gmy"),
                                                        SubWord.of("Class"),
                                                        SubWord.of("_"),
                                                        ])])]
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
