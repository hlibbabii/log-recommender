import unittest

from logrec.config.cl_default_config import classifier_config
from logrec.config.patch import patch_config


class PatchTest(unittest.TestCase):
    def test_patch(self):
        changed_config = patch_config(classifier_config, {'training.lrs.base_lr': 1000.0})

        self.assertEqual(changed_config.training.lrs.base_lr, 1000)

    def test_patch_no_attribute1(self):
        with self.assertRaises(AttributeError):
            patch_config(classifier_config, {'training.lrs.not_existent_attr': 1000.0})

    def test_patch_no_attribute2(self):
        with self.assertRaises(AttributeError):
            patch_config(classifier_config, {'not_existent_attr.lrs.base_lr': 1000.0})


if __name__ == '__main__':
    unittest.main()
