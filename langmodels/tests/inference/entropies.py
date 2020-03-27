import unittest
from unittest.mock import patch

from langmodels.inference.entropies import word_entropy_list, subword_average, word_average, file_fitter, get_lines, \
    unpackage_entropies


class WordEntropyListTest(unittest.TestCase):
    def test_invalid_empty_boundary_list(self):
        with self.assertRaises(ValueError):
            word_entropy_list([], [])

    def test_invalid_non_empty_boundary_list(self):
        with self.assertRaises(ValueError):
            word_entropy_list([0.1, 0.7, 8.6], [0, 2])

    def test_empty(self):
        self.assertEqual([], word_entropy_list([], [0]))

    def test_all_full_words(self):
        self.assertEqual([1.0, 2.0, 3.0], word_entropy_list([1.0, 2.0, 3.0], [0, 1, 2, 3]))

    def test_some_full_words(self):
        self.assertEqual([1.0, 5.0], word_entropy_list([1.0, 2.0, 3.0], [0, 1, 3]))

    def test_one_full_word(self):
        self.assertEqual([6.0], word_entropy_list([1.0, 2.0, 3.0], [0, 3]))


class SubwordAverageTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(.0, subword_average([], [0]))

    def test_not_empty(self):
        self.assertEqual(2.0, subword_average([1.0, 2.0, 3.0], [0, 1, 3]))


class WordAverageTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(.0, word_average([], [0]))

    def test_not_empty(self):
        self.assertEqual(3.0, word_average([1.0, 2.0, 3.0], [0, 1, 3]))


@patch("langmodels.inference.entropies.random.shuffle")
class FileFitterTest(unittest.TestCase):
    def test_simple(self, shuffle_mock):
        lst = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        actual = file_fitter(lst, 3)
        expected = [[0, 3, 6], [1, 4, 7], [2, 5, 8]]

        self.assertEqual(expected, actual)

    def test_invalid_n(self, shuffle_mock):
        with self.assertRaises(ValueError):
            file_fitter([], 0)

    def test_large_n(self, shuffle_mock):
        lst = [1, 2]
        actual = file_fitter(lst, 10)
        expected = [[0], [1], [], [], [], [], [], [], [], []]

        self.assertEqual(expected, actual)

    def test_n_equal_to_1(self, shuffle_mock):
        lst = [1, 2, 5, 6]
        actual = file_fitter(lst, 1)
        expected = [[0, 1, 2, 3]]

        self.assertEqual(expected, actual)


@patch("langmodels.inference.entropies.os.path.isfile")
@patch("langmodels.inference.entropies.get_list_of_line_lists_from_dir")
@patch("langmodels.inference.entropies.get_max_batch_size")
class GetLinesTest(unittest.TestCase):
    def test_simple(self, get_max_bs_mock, get_list_mock, isfile_mock):
        isfile_mock.return_value = False
        get_list_mock.return_value = [['a'], ['b'], ['c', 'd'], ['e', 'f'], ['g', 'h', 'j']]
        get_max_bs_mock.return_value = 3

        actual = get_lines("dir")
        expected = [['a', 'b', 'c'], ['e', 'g', 'd'], ['f', 'h', '\n'], ['\n', 'j', '\n']]

        self.assertEqual(expected, actual)


class UnpackageEntropiesTest(unittest.TestCase):
    def test_simple(self):
        entropies = [[1., 2., 3.], [4., 5., 6.], [7., 8., 9.], [10., 11., 12.]]
        files = [['a.txt', 'b.txt'], ['c.txt'], ['d.txt'], ['e.txt']]
        boundaries = [[0, 1, 3], [0, 3], [0, 2], [0, 1]]

        expected = {'a.txt': [1.], 'b.txt': [2., 3.], 'c.txt': [4., 5., 6.], 'd.txt': [7., 8.], 'e.txt': [10.],}
        actual = unpackage_entropies(entropies, files, boundaries)

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()