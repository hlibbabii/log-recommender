import unittest

from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
from logrec.dataprep.preprocessors.model.general import ProcessableToken, NonEng
from logrec.dataprep.preprocessors.model.numeric import Number, DecimalPoint
from logrec.dataprep.preprocessors.model.split import UnderscoreSplit, CamelCaseSplit, WithNumbersSplit
from logrec.dataprep.preprocessors.model.textcontainers import OneLineComment, StringLiteral, MultilineComment
# TODO write explanations with normal strings
from logrec.dataprep.preprocessors.preprocessing_types import PreprocessingParam
from logrec.dataprep.preprocessors.repr import to_repr
from logrec.dataprep.split.ngram import NgramSplittingType, NgramSplittingConfig


class TeprTest(unittest.TestCase):

    def test_both_bsr_and_bpe(self):
        with self.assertRaises(ValueError):
            prep_params = {PreprocessingParam.SPL_TYPE: 4,
                           PreprocessingParam.NO_NEWLINES_TABS: True,
                           PreprocessingParam.NO_STR: False,
                           PreprocessingParam.NO_COM: False,
                           PreprocessingParam.EN_ONLY: True,
                           PreprocessingParam.BSR: True
                           }
            to_repr(prep_params, [], {})

    ############################################################################################
    ############################################################################################

    def test_both_bsr_and_same_case_splitting(self):
        with self.assertRaises(ValueError):
            prep_params = {PreprocessingParam.SPL_TYPE: 3,
                           PreprocessingParam.NO_NEWLINES_TABS: True,
                           PreprocessingParam.NO_STR: False,
                           PreprocessingParam.NO_COM: False,
                           PreprocessingParam.EN_ONLY: True,
                           PreprocessingParam.BSR: True
                           }
            to_repr(prep_params, [], {})

    ############################################################################################
    ############################################################################################

    def test_to_repr_0(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 0,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: False,
                       }

        ngramSplittingConfig = NgramSplittingConfig()

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng(ProcessableToken("wirklich"))
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1.1',
            "*",
            '<non_eng>',
            '"', 'AWirklich', '"',
            '/*', '<non_eng>', 'blanco_english', '*/',
            '//', "Dieselbe8"
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_1(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 1,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: False,
                       }

        ngramSplittingConfig = NgramSplittingConfig()

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng(ProcessableToken("wirklich"))
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1.1',
            "*",
            '<non_eng>',
            '"', '`C', 'a', '<cc_sep>', '<non_eng>', '"',
            '/*', '<non_eng>', '<non_eng>', '<us_sep>', 'english', '*/',
            '//', '`C', '<non_eng>', '<cc_sep>', "8"
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_1_bsr(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 1,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: True,
                       }

        ngramSplittingConfig = NgramSplittingConfig()

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng(ProcessableToken("wirklich"))
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1.1',
            "*",
            '<non_eng>',
            '"', '`s', '`C', 'a', '<non_eng>', 's`', '"',
            '/*', '<non_eng>', '`s', '<non_eng>', 'english', 's`', '*/',
            '//', '`s', '`C', '<non_eng>', "8", 's`'
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_2(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 2,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: False,
                       }

        ngramSplittingConfig = NgramSplittingConfig(splitting_type=NgramSplittingType.ONLY_NUMBERS,
                                                    sc_splittings={
                                                        'english': ['engl', 'ish'],
                                                        '<non_eng>': ['<non', '_eng>']
                                                    })

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng(ProcessableToken("wirklich"))
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            '<sc_sep>',
            '.',
            '<sc_sep>',
            '1',
            "*",
            '<non_eng>',
            '"', '`C', 'a', '<cc_sep>', '<non_eng>', '"',
            '/*', '<non_eng>', '<non_eng>', '<us_sep>', 'english', '*/',
            '//', '`C', '<non_eng>', '<cc_sep>', "8",
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_2_bsr(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 2,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: True,
                       }

        ngramSplittingConfig = NgramSplittingConfig(splitting_type=NgramSplittingType.ONLY_NUMBERS)

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng(ProcessableToken("wirklich"))
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '`s',
            '1',
            '.',
            '1',
            's`',
            "*",
            '<non_eng>',
            '"', '`s', '`C', 'a', '<non_eng>', 's`', '"',
            '/*', '<non_eng>', '`s', '<non_eng>', 'english', 's`', '*/',
            '//', '`s', '`C', '<non_eng>', "8", 's`'
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_with_enonlycontents(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 3,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: False,
                       }

        ngramSplittingConfig = NgramSplittingConfig(splitting_type=NgramSplittingType.CUSTOM,
                                                    sc_splittings={})

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                NonEng(ProcessableToken("ich")),
                NonEng(ProcessableToken("weiss")),
                NonEng(ProcessableToken("nicht")),
                NonEng(ProcessableToken("was")),
                NonEng(ProcessableToken("soll")),
                NonEng(ProcessableToken("es")),
                NonEng(ProcessableToken("bedeuten")),
                NonEng(ProcessableToken("dass")),
                NonEng(ProcessableToken("ich")),
                NonEng(ProcessableToken("so")),
                NonEng(ProcessableToken("traurig")),
                NonEng(ProcessableToken("bin")),
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            '<sc_sep>',
            '.',
            '<sc_sep>',
            '1',
            "*",
            '<non_eng>',
            '"', '<non_eng_contents>', '"',
            '/*', '<non_eng>', '<non_eng>', '<us_sep>', 'english', '*/',
            '//', '`C', '<non_eng>', '<cc_sep>', "8",
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_3(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 3,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: False,
                       }

        ngramSplittingConfig = NgramSplittingConfig(splitting_type=NgramSplittingType.CUSTOM,
                                                    sc_splittings={
                                  'english': ['engl', 'ish'],
                                  '<non_eng>': ['<non', '_eng>']
                                                    })

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng(ProcessableToken("wirklich"))
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            '<sc_sep>',
            '.',
            '<sc_sep>',
            '1',
            "*",
            '<non_eng>',
            '"', '`C', 'a', '<cc_sep>', '<non_eng>', '"',
            '/*', '<non_eng>', '<non_eng>', '<us_sep>', 'engl', '<sc_sep>', 'ish', '*/',
            '//', '`C', '<non_eng>', '<cc_sep>', "8"
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_with_non_eng(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 3,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: False,
                       PreprocessingParam.BSR: False,
                       }

        ngramSplittingConfig = NgramSplittingConfig(splitting_type=NgramSplittingType.CUSTOM,
                                                    sc_splittings={
                                  'english': ['engl', 'ish'],
                                  'dieselbe': ['die', 'selbe'],
                                  '<non_eng>': ['<non', '_eng>']
                                                    })

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng("wirklich")
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            '<sc_sep>',
            '.',
            '<sc_sep>',
            '1',
            "*",
            'dinero',
            '"', '`C', 'a', '<cc_sep>', 'wirklich', '"',
            '/*', 'ц', 'blanco', '<us_sep>', 'engl', '<sc_sep>', 'ish', '*/',
            '//', '`C', 'die', '<sc_sep>', 'selbe', '<cc_sep>', "8",
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_with_newlines_and_tabs(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 2,
                       PreprocessingParam.NO_NEWLINES_TABS: False,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: True,
                       }

        ngramSplittingConfig = NgramSplittingConfig(splitting_type=NgramSplittingType.ONLY_NUMBERS,
                                                    )

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng(ProcessableToken("wirklich"))
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '`s',
            '1',
            '.',
            '1',
            's`',
            "*",
            '<non_eng>',
            '"', '`s', '`C', 'a', '<non_eng>', 's`', '"',
            '\n',
            '/*', '<non_eng>', '`s', '<non_eng>', 'english', 's`', '*/',
            '\n', '\t',
            '//', '`s', '`C', '<non_eng>', "8", 's`'
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_no_str_no_com(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 3,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: True,
                       PreprocessingParam.NO_COM: True,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: False,
                       }

        ngramSplittingConfig = NgramSplittingConfig(splitting_type=NgramSplittingType.CUSTOM,
                                                    sc_splittings={
                                  'english': ['engl', 'ish'],
                                  '<non_eng>': ['<non', '_eng>']
                                                    })

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng(ProcessableToken("wirklich"))
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            '<sc_sep>',
            '.',
            '<sc_sep>',
            '1',
            "*",
            '<non_eng>',
            '<str_literal>',
            '<comment>',
            '<comment>'
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_no_bsr(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 3,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: False,
                       }

        ngramSplittingConfig = NgramSplittingConfig(splitting_type=NgramSplittingType.CUSTOM,
                                                    sc_splittings={
                                  'english': ['engl', 'ish'],
                                  '<non_eng>': ['<non', '_eng>']
                                                    })

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng(ProcessableToken("wirklich"))
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            '<sc_sep>',
            '.',
            '<sc_sep>',
            '1',
            "*",
            '<non_eng>',
            '"', '`C', 'a', '<cc_sep>', '<non_eng>', '"',
            '/*', '<non_eng>', '<non_eng>', '<us_sep>', 'engl', '<sc_sep>', 'ish', '*/',
            '//', '`C', '<non_eng>', '<cc_sep>', "8"
        ]

        self.assertEqual(expected, actual)

    ############################################################################################
    ############################################################################################

    def test_to_repr_no_bsr_with_bpe_no_merges(self):
        prep_params = {PreprocessingParam.SPL_TYPE: 4,
                       PreprocessingParam.NO_NEWLINES_TABS: True,
                       PreprocessingParam.NO_STR: False,
                       PreprocessingParam.NO_COM: False,
                       PreprocessingParam.EN_ONLY: True,
                       PreprocessingParam.BSR: False,
                       }

        ngramSplittingConfig = NgramSplittingConfig(splitting_type=NgramSplittingType.BPE,
                                                    merges=[], merges_cache={})

        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng(ProcessableToken("dinero")),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng(ProcessableToken("wirklich"))
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng(ProcessableToken('ц')),
                UnderscoreSplit([
                    NonEng(ProcessableToken("blanco")),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng(ProcessableToken("dieselbe")),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens, ngramSplittingConfig)

        expected = [
            '1',
            '<sc_sep>', '.', '<sc_sep>',
            '1',
            "*",
            '<non_eng>',
            '"', '`C', 'a', '<cc_sep>', '<non_eng>', '"',
            '/*', '<non_eng>', '<non_eng>', '<us_sep>', 'e', '<sc_sep>', 'n', '<sc_sep>', 'g', '<sc_sep>', 'l',
            '<sc_sep>', 'i', '<sc_sep>', 's', '<sc_sep>', 'h', '*/',
            '//', '`C', '<non_eng>', '<cc_sep>', "8"
        ]

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
