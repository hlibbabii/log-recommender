import unittest

from logrec.infrastructure.fractions_manager import included_in_fraction


class FractionsManagerTest(unittest.TestCase):
    def test_include_to_df_smoke_true(self):
        result = included_in_fraction('120_file', 50.0, 0.0)

        self.assertTrue(result)

    def test_include_to_df_smoke_false(self):
        result = included_in_fraction('120_file', 50.0, 50.0)

        self.assertFalse(result)

    def test_include_to_df_zero_chunk_true(self):
        result = included_in_fraction('0_file', 0.1, 0.0)

        self.assertTrue(result)

    def test_include_to_df_zero_chunk_false(self):
        result = included_in_fraction('0_file', 0.1, 0.1)

        self.assertFalse(result)

    def test_include_to_df_999(self):
        result = included_in_fraction('999_file', 0.1, 99.9)

        self.assertTrue(result)

    def test_include_to_df_zero_percent(self):
        with self.assertRaises(ValueError):
            included_in_fraction('990_file', 0.0, 99.0)

    def test_include_to_df_invalid_percent(self):
        with self.assertRaises(ValueError):
            included_in_fraction('30_file', 101, 99.9)

    def test_include_to_df_invalid_start_from(self):
        with self.assertRaises(ValueError):
            included_in_fraction('file', 0.1, 150)

    def test_include_to_df_invalid_filename(self):
        with self.assertRaises(ValueError):
            included_in_fraction('file', 0.1, 99.9)


if __name__ == '__main__':
    unittest.main()
