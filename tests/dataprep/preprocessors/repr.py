import unittest

from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
# TODO write explanations with normal strings
from logrec.dataprep.preprocessors.model.containers import SplitContainer, OneLineComment, MultilineComment, \
    StringLiteral
from logrec.dataprep.preprocessors.model.noneng import NonEng
from logrec.dataprep.preprocessors.model.numeric import DecimalPoint, Number
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.preprocessors.model.word import FullWord, SubWord
from logrec.dataprep.preprocessors.preprocessing_types import PreprocessingParam
from logrec.dataprep.split.ngram import NgramSplittingType, NgramSplitConfig
from logrec.dataprep.to_repr import to_repr

tokens = [
    Number([1, DecimalPoint(), 1]),
    "*",
    NonEng(FullWord.of("dinero")),
    StringLiteral([
        SplitContainer([
            SubWord.of("A"),
            NonEng(SubWord.of("Wirklich"))
        ])
    ]),
    NewLine(),
    MultilineComment([
        NonEng(FullWord.of('ц')),
        SplitContainer([
            NonEng(SubWord.of("blanco")),
            SubWord.of("_english")
        ])
    ]),
    NewLine(), Tab(),
    OneLineComment([
        SplitContainer([
            NonEng(SubWord.of("DIESELBE")),
            SubWord.of("8")
        ])
    ])
]


class TeprTest(unittest.TestCase):

    def test_both_enonly_and_nosplit(self):
        with self.assertRaises(ValueError):
            prep_params = {
                PreprocessingParam.EN_ONLY: 1,
                PreprocessingParam.NO_COM_STR: 0,
                PreprocessingParam.SPL: 0,
                PreprocessingParam.NO_SEP: 0,
                PreprocessingParam.NO_NEWLINES_TABS: 1,
                PreprocessingParam.NO_LOGS: 0
            }
            to_repr(prep_params, [], {})

    def test_to_repr_0(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 0,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 0,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
            PreprocessingParam.NO_LOGS: 0
        }

        actual = to_repr(prep_params, tokens, NgramSplitConfig())

        expected = [
            '1.1',
            "*",
            'dinero',
            '"', 'AWirklich', '"',
            '/*', 'ц', 'blanco_english', '*/',
            '//', "DIESELBE8"
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_1(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 1,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
            PreprocessingParam.NO_LOGS: 0
        }

        actual = to_repr(prep_params, tokens, NgramSplitConfig())

        expected = [
            '1.1',
            "*",
            placeholders['non_eng'],
            '"', placeholders['capital'], 'a', placeholders["camel_case_separator"], placeholders['non_eng'], '"',
            '/*', placeholders['non_eng'], placeholders['non_eng'], placeholders["underscore_separator"], 'english',
            '*/',
            '//', placeholders['capitals'], placeholders['non_eng'], placeholders["camel_case_separator"], "8"
        ]

        self.assertEqual(expected, actual)

    #
    #     ############################################################################################
    #     ############################################################################################
    #
    def test_to_repr_1_nosep(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 1,
            PreprocessingParam.NO_SEP: 1,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
            PreprocessingParam.NO_LOGS: 0
        }

        actual = to_repr(prep_params, tokens, NgramSplitConfig())

        expected = [
            '1.1',
            "*",
            placeholders['non_eng'],
            '"', placeholders["camel_case_separator"], placeholders['capital'], 'a',
            placeholders["camel_case_separator"], placeholders['non_eng'], placeholders['split_words_end'], '"',
            '/*', placeholders['non_eng'], placeholders["camel_case_separator"], placeholders['non_eng'],
            placeholders["underscore_separator"], 'english', placeholders['split_words_end'], '*/',
            '//', placeholders["camel_case_separator"], placeholders['capitals'], placeholders['non_eng'],
            placeholders["camel_case_separator"], '8', placeholders['split_words_end']
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ########################k####################################################################

    def test_to_repr_2(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 2,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
            PreprocessingParam.NO_LOGS: 0
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.ONLY_NUMBERS,
                                                sc_splittings={})

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            placeholders["same_case_separator"],
            '.',
            placeholders["same_case_separator"],
            '1',
            "*",
            placeholders['non_eng'],
            '"', placeholders['capital'], 'a', placeholders["camel_case_separator"], placeholders['non_eng'], '"',
            '/*', placeholders['non_eng'], placeholders['non_eng'], placeholders["underscore_separator"], 'english',
            '*/',
            '//', placeholders['capitals'], placeholders['non_eng'], placeholders["camel_case_separator"], "8",
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_2_nosep(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 2,
            PreprocessingParam.NO_SEP: 1,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
            PreprocessingParam.NO_LOGS: 0
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.ONLY_NUMBERS)

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            placeholders["camel_case_separator"],
            '1',
            '.',
            '1',
            placeholders['split_words_end'],
            "*",
            placeholders['non_eng'],
            '"', placeholders["camel_case_separator"], placeholders['capital'], 'a',
            placeholders["camel_case_separator"], placeholders['non_eng'], placeholders['split_words_end'], '"',
            '/*', placeholders['non_eng'], placeholders["camel_case_separator"], placeholders['non_eng'],
            placeholders["underscore_separator"], 'english', placeholders['split_words_end'], '*/',
            '//', placeholders["camel_case_separator"], placeholders['capitals'], placeholders['non_eng'],
            placeholders["camel_case_separator"], "8", placeholders['split_words_end']
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_with_enonlycontents(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 3,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
            PreprocessingParam.NO_LOGS: 0
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.NUMBERS_AND_CUSTOM,
                                                sc_splittings={})

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(FullWord.of("dinero")),
            StringLiteral([
                NonEng(SubWord.of("ich")),
                NonEng(SubWord.of("weiss")),
                NonEng(SubWord.of("nicht")),
                NonEng(SubWord.of("was")),
                NonEng(SubWord.of("soll")),
                NonEng(SubWord.of("es")),
                NonEng(SubWord.of("bedeuten")),
                NonEng(SubWord.of("dass")),
                NonEng(SubWord.of("ich")),
                NonEng(SubWord.of("so")),
                NonEng(SubWord.of("traurig")),
                NonEng(SubWord.of("bin")),
            ]),
            NewLine(),
            MultilineComment([
                NonEng(FullWord.of('ц')),
                SplitContainer([
                    NonEng(SubWord.of("blanco")),
                    SubWord.of("_english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                SplitContainer([
                    NonEng(SubWord.of("DIESELBE")),
                    SubWord.of("8")
                ])
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            placeholders["same_case_separator"],
            '.',
            placeholders["same_case_separator"],
            '1',
            "*",
            placeholders['non_eng'],
            '"', placeholders["non_eng_contents"], '"',
            '/*', placeholders['non_eng'], placeholders['non_eng'], placeholders["underscore_separator"], 'english',
            '*/',
            '//', placeholders['capitals'], placeholders['non_eng'], placeholders["camel_case_separator"], "8",
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_3(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.SPL: 3,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
            PreprocessingParam.NO_LOGS: 0
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.NUMBERS_AND_CUSTOM,
                                                sc_splittings={
                                                    'english': ['engl', 'ish']
                                                    })

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            placeholders["same_case_separator"],
            '.',
            placeholders["same_case_separator"],
            '1',
            "*",
            placeholders['non_eng'],
            '"', placeholders['capital'], 'a', placeholders["camel_case_separator"], placeholders['non_eng'], '"',
            '/*', placeholders['non_eng'], placeholders['non_eng'], placeholders["underscore_separator"], 'engl',
            placeholders["same_case_separator"], 'ish', '*/',
            '//', placeholders['capitals'], placeholders['non_eng'], placeholders["camel_case_separator"], "8"
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_with_non_eng(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 0,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 3,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
            PreprocessingParam.NO_LOGS: 0
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.NUMBERS_AND_CUSTOM,
                                                sc_splittings={
                                  'english': ['engl', 'ish'],
                                                    'dieselbe': ['die', 'selbe']
                                                    })

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            placeholders["same_case_separator"],
            '.',
            placeholders["same_case_separator"],
            '1',
            "*",
            'dinero',
            '"', placeholders['capital'], 'a', placeholders["camel_case_separator"], 'wirklich', '"',
            '/*', 'ц', 'blanco', placeholders["underscore_separator"], 'engl', placeholders["same_case_separator"],
            'ish', '*/',
            '//', placeholders['capitals'], 'die', placeholders["same_case_separator"], 'selbe',
            placeholders["camel_case_separator"], "8",
        ]

        self.assertEqual(expected, actual)

    #
    #     ############################################################################################
    #     ############################################################################################
    #
    def test_to_repr_with_newlines_and_tabs(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 2,
            PreprocessingParam.NO_SEP: 1,
            PreprocessingParam.NO_NEWLINES_TABS: 0,
            PreprocessingParam.NO_LOGS: 0
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.ONLY_NUMBERS,
                                                )

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            placeholders["camel_case_separator"],
            '1',
            '.',
            '1',
            placeholders['split_words_end'],
            "*",
            placeholders['non_eng'],
            '"', placeholders["camel_case_separator"], placeholders['capital'], 'a',
            placeholders["camel_case_separator"], placeholders['non_eng'], placeholders['split_words_end'], '"',
            '\n',
            '/*', placeholders['non_eng'], placeholders["camel_case_separator"], placeholders['non_eng'],
            placeholders["underscore_separator"], 'english', placeholders['split_words_end'], '*/',
            '\n', '\t',
            '//', placeholders["camel_case_separator"], placeholders['capitals'], placeholders['non_eng'],
            placeholders["camel_case_separator"], "8", placeholders['split_words_end']
        ]

        self.assertEqual(expected, actual)

    #
    #     ############################################################################################
    #     ############################################################################################
    #
    def test_to_repr_no_str_no_com(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.NO_COM_STR: 2,
            PreprocessingParam.SPL: 3,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
            PreprocessingParam.NO_LOGS: 0
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.NUMBERS_AND_CUSTOM,
                                                sc_splittings={
                                                    'english': ['engl', 'ish']
                                                    })

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            placeholders["same_case_separator"],
            '.',
            placeholders["same_case_separator"],
            '1',
            "*",
            placeholders['non_eng'],
            placeholders["string_literal"],
            placeholders["comment"],
            placeholders["comment"]
        ]

        self.assertEqual(expected, actual)

    #
    #     ############################################################################################
    #     ############################################################################################
    #
    def test_to_repr_no_nosep(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 3,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: True,
            PreprocessingParam.NO_LOGS: 0
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.NUMBERS_AND_CUSTOM,
                                                sc_splittings={
                                                    'english': ['engl', 'ish']
                                                    })

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            placeholders["same_case_separator"],
            '.',
            placeholders["same_case_separator"],
            '1',
            "*",
            placeholders['non_eng'],
            '"', placeholders['capital'], 'a', placeholders["camel_case_separator"], placeholders['non_eng'], '"',
            '/*', placeholders['non_eng'], placeholders['non_eng'], placeholders["underscore_separator"], 'engl',
            placeholders["same_case_separator"], 'ish', '*/',
            '//', placeholders['capitals'], placeholders['non_eng'], placeholders["camel_case_separator"], "8"
        ]

        self.assertEqual(expected, actual)

    #
    #     ############################################################################################
    #     ############################################################################################
    #
    def test_to_repr_no_no_sep_with_bpe_no_merges(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 4,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
            PreprocessingParam.NO_LOGS: 0
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.BPE,
                                                merges=[], merges_cache={})

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            placeholders["same_case_separator"], '.', placeholders["same_case_separator"],
            '1',
            "*",
            placeholders['non_eng'],
            '"', placeholders['capital'], 'a', placeholders["camel_case_separator"], placeholders['non_eng'], '"',
            '/*', placeholders['non_eng'], placeholders['non_eng'], placeholders["underscore_separator"], 'e',
            placeholders["same_case_separator"], 'n', placeholders["same_case_separator"], 'g',
            placeholders["same_case_separator"], 'l',
            placeholders["same_case_separator"], 'i', placeholders["same_case_separator"], 's',
            placeholders["same_case_separator"], 'h', '*/',
            '//', placeholders['capitals'], placeholders['non_eng'], placeholders["camel_case_separator"], "8"
        ]

        self.assertEqual(expected, actual)

    #
    #
    # #################################################
    # ###   Only tests with single word go below
    # #################################################
    #
    def test_1(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 0,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 4,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 0,
            PreprocessingParam.NO_LOGS: 0
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.BPE,
                                                merges_cache={'while': ['while']})

        tokens = [FullWord.of("While")]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [placeholders['capital'], "while"]

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
