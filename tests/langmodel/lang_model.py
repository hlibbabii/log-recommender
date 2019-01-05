import unittest

from logrec.langmodel import lang_model


class LangModelTest(unittest.TestCase):
    # TODO these are only smoke tests, they should be improved by adding different checks after code being tested is run
    def test_lang_model_smoke(self):
        lang_model.run(find_lr=False, force_rerun=False)

    def test_lang_model_force_rerun_smoke(self):
        lang_model.run(find_lr=False, force_rerun=True)

    def test_lang_model_lr_finder_smoke(self):
        lang_model.run(find_lr=True, force_rerun=False)


if __name__ == '__main__':
    unittest.main()
