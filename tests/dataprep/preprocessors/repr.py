import unittest

from logrec.dataprep.preprocessors.model.chars import NewLine, Tab
from logrec.dataprep.preprocessors.model.general import ProcessableToken, NonEng
from logrec.dataprep.preprocessors.model.numeric import Number, DecimalPoint
from logrec.dataprep.preprocessors.model.split import UnderscoreSplit, CamelCaseSplit, WithNumbersSplit
from logrec.dataprep.preprocessors.model.textcontainers import OneLineComment, StringLiteral, MultilineComment
# TODO write explanations with normal strings
from logrec.dataprep.preprocessors.preprocessing_types import PreprocessingType
from logrec.dataprep.preprocessors.repr import to_repr


class TeprTest(unittest.TestCase):
    def test_to_repr_empty_preprocess_param_set(self):
        prep_params = {PreprocessingType.BSR: False}
        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng("wirklich")
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(),
            Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens)

        expected = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral([
                CamelCaseSplit([
                    "a",
                    NonEng("wirklich")
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    "english"
                ])
            ]),
            NewLine(),
            Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    "8"
                ], True)
            ])
        ]

        self.assertEqual(expected, actual)

    def test_to_repr_spl_1(self):
        prep_params = {PreprocessingType.SPL: True, PreprocessingType.BSR: False}
        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng("wirklich")
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens)

        expected = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral(['`C', 'a', '<cc_sep>', NonEng("wirklich")]),
            NewLine(),
            MultilineComment([NonEng('ц'), NonEng("blanco"), "<us_sep>", "english"]),
            NewLine(), Tab(),
            OneLineComment(['`C', NonEng("dieselbe"), '<cc_sep>', "8"])
        ]

        self.assertEqual(expected, actual)

    def test_to_repr_spl_1_numspl_1(self):
        prep_params = {PreprocessingType.SPL: True, PreprocessingType.NUM_SPL: True, PreprocessingType.BSR: False}
        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng("wirklich")
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens)

        expected = [
            '1',
            '<dec_point>',
            '1',
            "*",
            NonEng("dinero"),
            StringLiteral(['`C', 'a', '<cc_sep>', NonEng("wirklich")]),
            NewLine(),
            MultilineComment([NonEng('ц'), NonEng("blanco"), "<us_sep>", "english"]),
            NewLine(), Tab(),
            OneLineComment(['`C', NonEng("dieselbe"), '<cc_sep>', "8"])
        ]

        self.assertEqual(expected, actual)

    def test_to_repr_spl_1_numspl_1_nonewlinestabs_1(self):
        prep_params = {PreprocessingType.SPL: True, PreprocessingType.NUM_SPL: True,
                       PreprocessingType.NO_NEWLINES_TABS: True, PreprocessingType.BSR: False}
        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng("wirklich")
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens)

        expected = [
            '1',
            '<dec_point>',
            '1',
            "*",
            NonEng("dinero"),
            StringLiteral(['`C', 'a', '<cc_sep>', NonEng("wirklich")]),
            MultilineComment([NonEng('ц'), NonEng("blanco"), "<us_sep>", "english"]),
            OneLineComment(['`C', NonEng("dieselbe"), '<cc_sep>', "8"])
        ]

        self.assertEqual(expected, actual)

    def test_to_repr_spl_1_numspl_1_nonewlinestabs_1_nostr_1(self):
        prep_params = {PreprocessingType.SPL: True, PreprocessingType.NUM_SPL: True,
                       PreprocessingType.NO_NEWLINES_TABS: True, PreprocessingType.NO_STR: True,
                       PreprocessingType.BSR: False}
        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng("wirklich")
                ], True)
            ]),
            StringLiteral([ProcessableToken("b")]),
            NewLine(),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens)

        expected = [
            '1',
            '<dec_point>',
            '1',
            "*",
            NonEng("dinero"),
            '<str_literal>', '<str_literal>',
            MultilineComment([NonEng('ц'), NonEng("blanco"), "<us_sep>", "english"]),
            OneLineComment(['`C', NonEng("dieselbe"), '<cc_sep>', "8"])
        ]

        self.assertEqual(expected, actual)

    def test_to_repr_spl_1_numspl_1_nonewlinestabs_1_nostr_0(self):
        prep_params = {PreprocessingType.SPL: True, PreprocessingType.NUM_SPL: True,
                       PreprocessingType.NO_NEWLINES_TABS: True, PreprocessingType.NO_STR: False,
                       PreprocessingType.BSR: False}
        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng("wirklich")
                ], True)
            ]),
            StringLiteral([ProcessableToken("b")]),
            NewLine(),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens)

        expected = [
            '1',
            '<dec_point>',
            '1',
            "*",
            NonEng("dinero"),
            '"', '`C', 'a', '<cc_sep>', NonEng("wirklich"), '"',
            '"', 'b', '"',
            MultilineComment([NonEng('ц'), NonEng("blanco"), "<us_sep>", "english"]),
            OneLineComment(['`C', NonEng("dieselbe"), '<cc_sep>', "8"])
        ]

        self.assertEqual(expected, actual)

    def test_to_repr_spl_1_numspl_1_nonewlinestabs_1_nostr_0_enonly_1(self):
        prep_params = {PreprocessingType.SPL: True,
                       PreprocessingType.NUM_SPL: True,
                       PreprocessingType.NO_NEWLINES_TABS: True,
                       PreprocessingType.NO_STR: False,
                       PreprocessingType.EN_ONLY: True,
                       PreprocessingType.BSR: False}
        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng("wirklich")
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens)

        expected = [
            '1',
            '<dec_point>',
            '1',
            "*",
            '<non_eng>',
            '"', '`C', 'a', '<cc_sep>', '<non_eng>', '"',
            MultilineComment(['<non_eng>', '<non_eng>', "<us_sep>", "english"]),
            OneLineComment(['`C', '<non_eng>', '<cc_sep>', "8"])
        ]

        self.assertEqual(expected, actual)

    def test_to_repr_spl_1_numspl_1_nonewlinestabs_1_nostr_0_enonly_1_with_enonlycontents(self):
        prep_params = {PreprocessingType.SPL: True,
                       PreprocessingType.NUM_SPL: True,
                       PreprocessingType.NO_NEWLINES_TABS: True,
                       PreprocessingType.NO_STR: False,
                       PreprocessingType.EN_ONLY: True,
                       PreprocessingType.BSR: False}
        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral([
                NonEng("ich"),
                NonEng("weiss"),
                NonEng("nicht"),
                NonEng("was"),
                NonEng("soll"),
                NonEng("es"),
                NonEng("bedeuten"),
                NonEng("dass"),
                NonEng("ich"),
                NonEng("so"),
                NonEng("traurig"),
                NonEng("bin"),
            ]),
            NewLine(),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens)

        expected = [
            '1',
            '<dec_point>',
            '1',
            "*",
            '<non_eng>',
            '"', '<non_eng_contents>', '"',
            MultilineComment(['<non_eng>', '<non_eng>', "<us_sep>", "english"]),
            OneLineComment(['`C', '<non_eng>', '<cc_sep>', "8"])
        ]

        self.assertEqual(expected, actual)

    def test_to_repr_spl_1_numspl_1_nonewlinestabs_1_nostr_0_enonly_1_bsr(self):
        prep_params = {PreprocessingType.SPL: True,
                       PreprocessingType.NUM_SPL: True,
                       PreprocessingType.NO_NEWLINES_TABS: True,
                       PreprocessingType.NO_STR: False,
                       PreprocessingType.EN_ONLY: True,
                       PreprocessingType.BSR: True}
        tokens = [
            Number([1, DecimalPoint(), 1]),
            "*",
            NonEng("dinero"),
            StringLiteral([
                CamelCaseSplit([
                    ProcessableToken("a"),
                    NonEng("wirklich")
                ], True)
            ]),
            NewLine(),
            MultilineComment([
                NonEng('ц'),
                UnderscoreSplit([
                    NonEng("blanco"),
                    ProcessableToken("english")
                ])
            ]),
            NewLine(), Tab(),
            OneLineComment([
                WithNumbersSplit([
                    NonEng("dieselbe"),
                    ProcessableToken("8")
                ], True)
            ])
        ]

        actual = to_repr(prep_params, tokens)

        expected = [
            '1',
            '<dec_point>',
            '1',
            "*",
            '<non_eng>',
            '"', '`s', '`C', 'a', '<non_eng>', 's`', '"',
            MultilineComment(['<non_eng>', '`s', '<non_eng>', "english", 's`']),
            OneLineComment(['`s', '`C', '<non_eng>', "8", 's`'])
        ]

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
