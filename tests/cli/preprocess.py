import unittest

from logrec.cli import preprocess
from logrec.dataprep.model.placeholders import placeholders

cap = placeholders['capital']
caps = placeholders['capitals']
ws = placeholders['word_start']
we = placeholders['word_end']


class PreprocessTest(unittest.TestCase):
    def test1_00000(self):
        token = "hideSoftInputFromWindow"

        actual = preprocess(token, '00000')

        self.assertEqual(['hideSoftInputFromWindow'], actual)

    def test1_10411(self):
        token = "hideSoftInputFromWindow"

        actual = preprocess(token, '10411')

        self.assertEqual([ws, 'hide', cap, 'soft', cap, 'input', cap, 'from', cap, 'window', we], actual)

    def test2_10411(self):
        token = "_currentReaderVersion"

        actual = preprocess(token, '10411')

        self.assertEqual([ws, '_', 'current', cap, 'reader', cap, 'version', we], actual)

    def test3_10411(self):
        token = "LAYOUT_INFLATER_SERVICE"

        actual = preprocess(token, '10411')

        self.assertEqual([ws, caps, 'layout', '_', caps, 'inflater', '_', caps, 'service', we], actual)

    def test4_10411(self):
        token = "appirate_utils_message_before_appname"

        actual = preprocess(token, '10411')

        self.assertEqual([ws, 'app', 'ir', 'ate', '_', 'utils', '_', 'message', '_', 'before', '_', 'app', 'name', we],
                         actual)

    def test5_10411(self):
        token = "MalformedURLException"

        actual = preprocess(token, '10411')

        self.assertEqual([ws, cap, 'malformed', caps, 'url', cap, 'exception', we], actual)

    def test6_10411(self):
        token = "PERSISTENCE_BUNDLE_A"

        actual = preprocess(token, '10411')

        self.assertEqual([ws, caps, 'persistence', '_', caps, 'bundle', '_', caps, 'a', we], actual)

    def test7_10411(self):
        token = "IImplicitRenderArgProvider"

        actual = preprocess(token, '10411')

        self.assertEqual([ws, caps, 'i', cap, 'implicit', cap, 'render', cap, 'arg', cap, 'provider', we], actual)

    def test8_10411(self):
        token = "__INCULDED_TEMPLATE_CLASS_NAME_LIST__"

        actual = preprocess(token, '10411')

        self.assertEqual(
            [ws, '_', '_', caps, 'inc', 'ul', 'ded', '_', caps, 'template', '_', caps, 'class', '_', caps, 'name', '_',
             caps, 'list', '_', '_', we], actual)

    def test9_10411(self):
        token = "cmd_reloadquestconfig"

        actual = preprocess(token, '10411')

        self.assertEqual([ws, 'cmd', '_', 'reload', 'quest', 'config', we], actual)

    def test10_10411(self):
        token = "_407_PROXY_AUTH_REQUIRED"

        actual = preprocess(token, '10411')

        self.assertEqual([ws, '_', '4', '07', '_', caps, 'proxy', '_', caps, 'auth', '_', caps, 'required', we], actual)

    def test11_10411(self):
        token = "HTTP_1_0_noConnectionHeaderTest"

        actual = preprocess(token, '10411')

        self.assertEqual(
            [ws, caps, 'http', '_', '1', '_', '0', '_', 'no', cap, 'connection', cap, 'header', cap, 'test', we],
            actual)

    def test12_10411(self):
        token = "f4_impact_1_original"

        actual = preprocess(token, '10411')

        self.assertEqual([ws, 'f', '4', '_', 'imp', 'act', '_', '1', '_', 'original', we], actual)


if __name__ == '__main__':
    unittest.main()
