import unittest
from functools import partial

from logrec.dataprep.preprocessors.model.general import ProcessableToken
from logrec.dataprep.preprocessors.model.split import UnderscoreSplit, CamelCaseSplit, WithNumbersSplit, SameCaseSplit
from logrec.dataprep.preprocessors.model.textcontainers import OneLineComment, MultilineComment, StringLiteral
from logrec.dataprep.preprocessors.split import apply_splitting_to_token, split_string_camel_case, \
    split_string_underscore, split_string_with_numbers


class SplitTest(unittest.TestCase):
    def test_camel_case_split(self):
        token = OneLineComment([UnderscoreSplit(
            [ProcessableToken("test"), ProcessableToken("MyClass")])])
        actual = apply_splitting_to_token(token, split_string_camel_case)

        expected = OneLineComment([UnderscoreSplit([ProcessableToken("test"),
                                                    CamelCaseSplit([ProcessableToken("my"),
                                                                    ProcessableToken("class")], True)])])
        self.assertEqual(actual, expected)

    def test_camel_case_split_lowercase(self):
        token = OneLineComment([UnderscoreSplit(
            [ProcessableToken("test"), ProcessableToken("myClass")])])
        actual = apply_splitting_to_token(token, split_string_camel_case)

        expected = OneLineComment([UnderscoreSplit([ProcessableToken("test"),
                                                    CamelCaseSplit([ProcessableToken("my"),
                                                                    ProcessableToken("class")], False)])])
        self.assertEqual(actual, expected)


    def test_underscore_split(self):
        token = MultilineComment([CamelCaseSplit(
            [ProcessableToken("my_class"), ProcessableToken("8"), ProcessableToken("ab")], True)])
        actual = apply_splitting_to_token(token, split_string_underscore)

        expected = MultilineComment([CamelCaseSplit(
            [UnderscoreSplit([ProcessableToken("my"),ProcessableToken("class")]), ProcessableToken("8"), ProcessableToken("ab")], True)])
        self.assertEqual(actual, expected)


    def test_with_numbers_split(self):
        token = StringLiteral([":", UnderscoreSplit([ProcessableToken("my"), ProcessableToken("123g"),ProcessableToken("victory")])])
        actual = apply_splitting_to_token(token, split_string_with_numbers)

        expected = StringLiteral([":", UnderscoreSplit([ProcessableToken("my"),
                                                        WithNumbersSplit([ProcessableToken("1"), ProcessableToken("2"), ProcessableToken("3"), ProcessableToken("g")], False),
                                                        ProcessableToken("victory")])])
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
