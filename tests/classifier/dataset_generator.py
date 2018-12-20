import unittest

from logrec.classifier.dataset_generator import create_case


class DataGeneratorTest(unittest.TestCase):
    def test_create_case_no_padding(self):
        lst = ['a'] * 5000
        position = 2000
        actual = create_case(lst, [position])

        expected = ['a'] * 1000, ['a'] * 1000
        self.assertEqual(expected, actual)

    def test_create_case_before_padding(self):
        lst = ['a'] * 5000
        position = 400
        actual = create_case(lst, [position])

        expected = ['<pad>'] * 600 + ['a'] * 400, ['a'] * 1000
        self.assertEqual(expected, actual)

    def test_create_case_after_padding(self):
        lst = ['a'] * 5000
        position = 4599
        actual = create_case(lst, [position])

        expected = ['a'] * 1000, ['a'] * 400 + ['<pad>'] * 600
        self.assertEqual(expected, actual)

    def test_create_case_before_and_after_padding(self):
        lst = ['a'] * 1001
        position = 400
        actual = create_case(lst, [position])

        expected = ['<pad>'] * 600 + ['a'] * 400, ['a'] * 600 + ['<pad>'] * 400
        self.assertEqual(expected, actual)

    def test_create_case_zero_position(self):
        lst = ['a'] * 5000
        position = 0
        actual = create_case(lst, [position])

        expected = ['<pad>'] * 1000, ['a'] * 1000
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
