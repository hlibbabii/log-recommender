import unittest

from logrec.infrastructure.fractions_manager import include_to_df


class FractionsManagerTest(unittest.TestCase):
    def test_include_to_df_smoke_true(self):
        result = include_to_df('120_file', 50.0, 0.0)

        self.assertTrue(result)

    def test_include_to_df_smoke_false(self):
        result = include_to_df('120_file', 50.0, 50.0)

        self.assertFalse(result)

    def test_include_to_df_zero_chunk_true(self):
        result = include_to_df('0_file', 0.1, 0.0)

        self.assertTrue(result)

    def test_include_to_df_zero_chunk_false(self):
        result = include_to_df('0_file', 0.1, 0.1)

        self.assertFalse(result)

    def test_include_to_df_999(self):
        result = include_to_df('999_file', 0.1, 99.9)

        self.assertTrue(result)

    def test_include_to_df_zero_percent(self):
        with self.assertRaises(ValueError):
            include_to_df('990_file', 0.0, 99.0)

    def test_include_to_df_invalid_percent(self):
        with self.assertRaises(ValueError):
            include_to_df('30_file', 101, 99.9)

    def test_include_to_df_invalid_start_from(self):
        with self.assertRaises(ValueError):
            include_to_df('file', 0.1, 150)

    def test_include_to_df_invalid_filename(self):
        with self.assertRaises(ValueError):
            include_to_df('file', 0.1, 99.9)


if __name__ == '__main__':
    unittest.main()
