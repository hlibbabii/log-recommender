import unittest

from torchtext.data import Field

from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.full_word_iterator import FullWordIterator

text_field = Field()
text_field.build_vocab([[
    placeholders['camel_case_separator'],
    placeholders['split_words_end'],
    placeholders['capital'],
    placeholders['capitals'],
    '}',
    'a',
    placeholders['underscore_separator'],
    placeholders['log_statement'],
    placeholders['info'],
    placeholders['log_statement_end']
]])


def iter_to_int_list(it):
    return [w for w in it]


class FullwordIteratorTest(unittest.TestCase):
    def test1(self):
        input_str = ['}', '}',
                     placeholders['log_statement'],
                     placeholders['info'],
                     placeholders['log_statement_end'],
                     placeholders['camel_case_separator'],
                     placeholders['capital'],
                     'a',
                     placeholders['camel_case_separator'],
                     'a',
                     placeholders['split_words_end'],
                     '}',
                     placeholders['capitals']]

        full_word_indexes = [(0, 1), (1, 2), (5, 11), (11, 12)]

        expected = [(input_str[range[0]: range[1]], range) for range in full_word_indexes]

        it = FullWordIterator(input_str)

        actual = iter_to_int_list(it)
        self.assertEqual(expected, actual)

        it.add_data(['a', placeholders['underscore_separator']])
        actual = iter_to_int_list(it)
        self.assertEqual(
            [([placeholders['capitals'], 'a'], (0, 2))], actual
        )

        it.add_data([placeholders['split_words_end']])
        actual = iter_to_int_list(it)
        self.assertEqual(
            [([placeholders['underscore_separator'], placeholders['split_words_end']], (0, 2))], actual
        )

    def test_empty(self):
        it = FullWordIterator([])

        actual = [i for i in it]
        self.assertEqual([], actual)

    def test_not_full_word(self):
        targets_str = [placeholders['capitals']]

        it = FullWordIterator(targets_str)

        actual = [i for i in it]
        self.assertEqual([], actual)


if __name__ == '__main__':
    unittest.main()
