import unittest

import torch
from unittest import TestCase

from logrec.langmodel.metrics import subword_aware_accuracy_strict, subword_aware_accuracy


class MetricsTest(TestCase):
    def test_subword_aware_accuracy_strict(self):
        predicted = torch.LongTensor([1, 2, 3, 4, 5])
        target = torch.LongTensor([1, 2, 0, 9, 5])
        full_words_mask = torch.ByteTensor([
            [1, 1, 1, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1],
        ])

        actual = subword_aware_accuracy_strict(predicted, target, full_words_mask)
        self.assertAlmostEqual(0.33, actual, 2)

    def test_subword_aware_accuracy(self):
        predicted = torch.LongTensor([1, 2, 3, 4, 5])
        target = torch.LongTensor([1, 2, 0, 9, 5])
        full_words_mask = torch.ByteTensor([
            [1, 1, 1, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1],
        ])

        actual = subword_aware_accuracy(predicted, target, full_words_mask)
        self.assertAlmostEqual(0.56, actual, 2)


if __name__ == '__main__':
    unittest.main()
