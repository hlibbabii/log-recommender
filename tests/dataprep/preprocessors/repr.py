import unittest

from logrec.dataprep.model.chars import NewLine, Tab
# TODO write explanations with normal strings
from logrec.dataprep.model.containers import SplitContainer, OneLineComment, MultilineComment, \
    StringLiteral
from logrec.dataprep.model.logging import INFO, LogStatement
from logrec.dataprep.model.noneng import NonEng, NonEngFullWord, NonEngSubWord
from logrec.dataprep.model.numeric import DecimalPoint, Number
from logrec.dataprep.model.placeholders import placeholders
from logrec.dataprep.model.word import FullWord, SubWord
from logrec.dataprep.prepparams import PreprocessingParam
from logrec.dataprep.split.ngram import NgramSplittingType, NgramSplitConfig
from logrec.dataprep.to_repr import to_repr

tokens = [
    Number([1, DecimalPoint(), 1]),
    "*",
    NonEngFullWord(FullWord.of("dinero")),
    StringLiteral([
        SplitContainer([
            SubWord.of("A"),
            NonEngSubWord(SubWord.of("Wirklich"))
        ])
    ]),
    NewLine(),
    MultilineComment([
        NonEngFullWord(FullWord.of('ц')),
        SplitContainer([
            NonEngSubWord(SubWord.of("blanco")),
            SubWord.of("_english")
        ])
    ]),
    NewLine(), Tab(),
    OneLineComment([
        SplitContainer([
            NonEngSubWord(SubWord.of("DIESELBE")),
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
            }
            to_repr(prep_params, [], NgramSplitConfig())

    def test_to_repr_0(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 0,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 0,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 1,
        }

        actual = to_repr(prep_params, tokens, NgramSplitConfig())

        expected = [
            '1.1',
            "*",
            'dinero',
            '"', 'AWirklich', '"',
            '/*', 'ц', 'blanco_english', '*/',
            '//', "DIESELBE8", placeholders['olc_end']
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
        }

        actual = to_repr(prep_params, tokens, NgramSplitConfig())

        expected = [
            '1.1',
            "*",
            placeholders['non_eng'],
            '"', placeholders['capital'], 'a', placeholders["camel_case_separator"], placeholders['non_eng'], '"',
            '/*', placeholders['non_eng'], placeholders['non_eng'], placeholders["underscore_separator"], 'english',
            '*/',
            '//', placeholders['capitals'], placeholders['non_eng'], placeholders["camel_case_separator"], "8",
            placeholders['olc_end']
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
            placeholders["camel_case_separator"], '8', placeholders['split_words_end'], placeholders['olc_end']
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
            placeholders['olc_end']
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
            placeholders["camel_case_separator"], "8", placeholders['split_words_end'], placeholders['olc_end']
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
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.NUMBERS_AND_CUSTOM,
                                                sc_splittings={})

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEngFullWord(FullWord.of("dinero")),
            StringLiteral([
                NonEngSubWord(SubWord.of("ich")),
                NonEngSubWord(SubWord.of("weiss")),
                NonEngSubWord(SubWord.of("nicht")),
                NonEngSubWord(SubWord.of("was")),
                NonEngSubWord(SubWord.of("soll")),
                NonEngSubWord(SubWord.of("es")),
                NonEngSubWord(SubWord.of("bedeuten")),
                NonEngSubWord(SubWord.of("dass")),
                NonEngSubWord(SubWord.of("ich")),
                NonEngSubWord(SubWord.of("so")),
                NonEngSubWord(SubWord.of("traurig")),
                NonEngSubWord(SubWord.of("bin")),
            ]),
            NewLine(),
            MultilineComment([
                NonEngFullWord(FullWord.of('ц')),
                SplitContainer([
                    NonEngSubWord(SubWord.of("blanco")),
                    SubWord.of("_english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                SplitContainer([
                    NonEngSubWord(SubWord.of("DIESELBE")),
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
            placeholders['olc_end']
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
            '//', placeholders['capitals'], placeholders['non_eng'], placeholders["camel_case_separator"], "8",
            placeholders['olc_end']
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
            placeholders["camel_case_separator"], "8", placeholders['olc_end']
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
            placeholders["camel_case_separator"], "8", placeholders['split_words_end'], placeholders['olc_end']
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
            '//', placeholders['capitals'], placeholders['non_eng'], placeholders["camel_case_separator"], "8",
            placeholders['olc_end']
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
            '//', placeholders['capitals'], placeholders['non_eng'], placeholders["camel_case_separator"], "8",
            placeholders['olc_end']
        ]

        self.assertEqual(expected, actual)

    def test_log(self):
        prep_params = {
            PreprocessingParam.EN_ONLY: 1,
            PreprocessingParam.NO_COM_STR: 0,
            PreprocessingParam.SPL: 1,
            PreprocessingParam.NO_SEP: 0,
            PreprocessingParam.NO_NEWLINES_TABS: 0,
        }

        ngramSplittingConfig = NgramSplitConfig()

        tokens = [LogStatement(FullWord.of('LOGGER'), FullWord.of('Info'), INFO, [StringLiteral([FullWord.of("Hi")])])]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [placeholders['log_statement'], '`info', '`Cs', 'logger', '.', '`C', 'info', '(', '"', '`C', 'hi',
                    '"', ')', ';', 'L`']

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
        }

        ngramSplittingConfig = NgramSplitConfig(splitting_type=NgramSplittingType.BPE,
                                                merges_cache={'while': ['while']})

        tokens = [FullWord.of("While")]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [placeholders['capital'], "while"]

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
