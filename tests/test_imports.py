import importlib
import os
import pkgutil
import unittest

from logrec.dataprep import base_project_dir


class ImportsTest(unittest.TestCase):
    @unittest.skip("Problems with torch import")
    def test_imports(self):
        importlib.import_module('torch')
        __all__ = []
        for loader, module_name, is_pkg in pkgutil.walk_packages([os.path.join(base_project_dir, "logrec")]):
            __all__.append(module_name)
            module = loader.find_module(module_name).load_module(module_name)
            globals()[module_name] = module
