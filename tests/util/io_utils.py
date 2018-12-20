import os
import unittest
from logrec.dataprep import base_project_dir
from logrec.util import io_utils

PATH_TO_TEST_DATA = f'{base_project_dir}/test-resources'
if not os.path.exists(PATH_TO_TEST_DATA):
    os.mkdir(PATH_TO_TEST_DATA)
PATH_TO_FILE = f'{PATH_TO_TEST_DATA}/dump-read-test.txt'


class IoUtilsTest(unittest.TestCase):
    def tearDown(self):
        os.remove(PATH_TO_FILE)

    def test_dump_read_dict(self):
        sample = {'key': 'value'}
        io_utils.dump_dict_into_2_columns(sample, PATH_TO_FILE)
        result = io_utils.read_dict_from_2_columns(PATH_TO_FILE)
        self.assertEqual(sample, result)

    def test_dump_read_dict_int_value(self):
        sample = {'key': 3}
        io_utils.dump_dict_into_2_columns(sample, PATH_TO_FILE)
        result = io_utils.read_dict_from_2_columns(PATH_TO_FILE)
        self.assertEqual(sample, result)

    def test_dump_read_dict_list_value(self):
        sample = {'key': ['value1', 'value2']}
        io_utils.dump_dict_into_2_columns(sample, PATH_TO_FILE, val_type=list)
        result = io_utils.read_dict_from_2_columns(PATH_TO_FILE, val_type=list)
        self.assertEqual(sample, result)

    def test_dump_read_dict_list_value_with_1_elm(self):
        sample = {'key': ['value1']}
        io_utils.dump_dict_into_2_columns(sample, PATH_TO_FILE, val_type=list)
        result = io_utils.read_dict_from_2_columns(PATH_TO_FILE, val_type=list)
        self.assertEqual(sample, result)

    def test_dump_read_dict_with_space_delim(self):
        sample = {'key': 'value1'}
        io_utils.dump_dict_into_2_columns(sample, PATH_TO_FILE, delim='|')
        result = io_utils.read_dict_from_2_columns(PATH_TO_FILE, delim='|')
        self.assertEqual(sample, result)

    def test_dump_read_list(self):
        sample = [['aa', 'bb', 'cc'], ['mm', 'hh', 'j']]
        io_utils.dump_list(sample, PATH_TO_FILE)
        result = io_utils.read_list(PATH_TO_FILE)
        self.assertEqual(sample, result)

    def test_dump_read_list_not_nested(self):
        sample = ['aa', 'bb', 'c']
        io_utils.dump_list(sample, PATH_TO_FILE)
        result = io_utils.read_list(PATH_TO_FILE)
        self.assertEqual(sample, result)


if __name__ == '__main__':
    unittest.main()
