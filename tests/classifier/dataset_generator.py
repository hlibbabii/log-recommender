import unittest

from logrec.classifier.dataset_generator import create_case, create_negative_case, create_positive_case, \
    get_possible_log_locations
from logrec.dataprep.preprocessors.model.placeholders import placeholders


class DataGeneratorTest(unittest.TestCase):
    def test_create_case_no_padding(self):
        lst = ['a'] * 5000
        position = 2000
        actual = create_case(lst, position)

        expected = ['a'] * 1000, ['a'] * 1000
        self.assertEqual(expected, actual)

    def test_create_case_before_padding(self):
        lst = ['a'] * 5000
        position = 400
        actual = create_case(lst, position)

        expected = placeholders['pad_token'] * 600 + ['a'] * 400, ['a'] * 1000
        self.assertEqual(expected, actual)

    def test_create_case_after_padding(self):
        lst = ['a'] * 5000
        position = 4599
        actual = create_case(lst, position)

        expected = ['a'] * 1000, ['a'] * 400 + [placeholders['pad_token']] * 600
        self.assertEqual(expected, actual)

    def test_create_case_before_and_after_padding(self):
        lst = ['a'] * 1001
        position = 400
        actual = create_case(lst, position)

        expected = [placeholders['pad_token']] * 600 + ['a'] * 400, ['a'] * 600 + [placeholders['pad_token']] * 400
        self.assertEqual(expected, actual)

    def test_create_case_zero_position(self):
        lst = ['fake_log', placeholders["loggable_block"]] + ['a'] * 5000
        position = 0
        actual = create_case(lst, position)

        expected = [placeholders['pad_token']] * 1000, ['a'] * 1000
        self.assertEqual(expected, actual)

    def test_create_negative_case(self):
        lst = [placeholders["loggable_block"], "int", "a", "=", "0", ";", "//", "comment",
               placeholders["loggable_block_end"]]

        actual = create_negative_case(lst)

        expected = [placeholders['pad_token']] * 995 + ["int", "a", "=", "0", ";"], \
                   ["//", "comment"] + [placeholders['pad_token']] * 998

        self.assertEqual(expected, actual)

    def test_create_negative_case_no_loggable_blocks(self):
        lst = ["int", "a", "=", "0", ";", "//", "comment"]

        actual = create_negative_case(lst)

        self.assertIsNone(actual)

    def test_create_positive_case(self):
        lst = [placeholders["loggable_block"], "int", "a", "=", "0", ";", placeholders['log_statement'], "//",
               "comment", placeholders["loggable_block_end"]]

        actual = create_positive_case(lst)

        expected = [placeholders['pad_token']] * 995 + ["int", "a", "=", "0", ";"], \
                   ["//", "comment"] + [placeholders['pad_token']] * 998

        self.assertEqual(expected, actual)

    def test_get_possible_log_locations(self):
        lst = [placeholders["loggable_block"], "{", "{",
               "int", "a", "=", "0", ";",
               "//", "comment",
               "}", "}", placeholders["loggable_block_end"],
               "int", "b", "=", "3",
               placeholders["loggable_block"], "{",
               "int", "a", "=", "0", ";",
               "//", "comment",
               "}", placeholders["loggable_block_end"]
               ]

        actual = get_possible_log_locations(lst)

        expected = [2, 3, 8, 11, 19, 24]

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
