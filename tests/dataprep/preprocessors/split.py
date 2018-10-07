import unittest

from dataprep.preprocessors.model.textcontainers import OneLineComment, MultilineComment, StringLiteral
from dataprep.preprocessors.split import *


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
        actual = apply_splitting_to_token(token, split_string_underscore())

        expected = MultilineComment([CamelCaseSplit(
            [UnderscoreSplit([ProcessableToken("my"),ProcessableToken("class")]), ProcessableToken("8"), ProcessableToken("ab")], True)])
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

    def test_same_case_split(self):
        token = CamelCaseSplit([ProcessableToken("mylovelyclass")], False)

        actual = apply_splitting_to_token(token, partial(split_string_same_case, {"mylovelyclass": ["my", 'lovely', "class"]}))

        expected = CamelCaseSplit([SameCaseSplit([ProcessableToken("my"), ProcessableToken("lovely"),
                                                 ProcessableToken("class")], False)], False)

        self.assertEqual(actual, expected)

    def test_same_case_split_no_split(self):
        token = CamelCaseSplit([ProcessableToken("mylovelyclass")], False)

        actual = apply_splitting_to_token(token, partial(split_string_same_case, {}))

        expected = CamelCaseSplit([ProcessableToken("mylovelyclass")], False)

        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
