import unittest

from dataprep.preprocessors.model.chars import NewLine, Tab
from dataprep.preprocessors.model.general import ProcessableToken, NonEng
from dataprep.preprocessors.model.numeric import Number, DecimalPoint
from dataprep.preprocessors.model.split import UnderscoreSplit, CamelCaseSplit, WithNumbersSplit
from dataprep.preprocessors.model.textcontainers import OneLineComment, StringLiteral, MultilineComment
# TODO write explanations with normal strings
from dataprep.preprocessors.preprocessing_types import PreprocessingType
from dataprep.preprocessors.repr import to_repr


class TeprTest(unittest.TestCase):
    def test_to_repr_empty_preprocess_param_set(self):
        prep_params = []
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
        prep_params = {PreprocessingType.SPL: True}
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
            StringLiteral(['<capital>', 'a', '<cc_sep>', NonEng("wirklich")]),
            NewLine(),
            MultilineComment([NonEng('ц'), NonEng("blanco"), "<us_sep>", "english"]),
            NewLine(), Tab(),
            OneLineComment(['<capital>', NonEng("dieselbe"), '<cc_sep>', "8"])
        ]

        self.assertEqual(expected, actual)

    def test_to_repr_spl_1_numspl_1(self):
        prep_params = {PreprocessingType.SPL: True, PreprocessingType.NUM_SPL: True}
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
            StringLiteral(['<capital>', 'a', '<cc_sep>', NonEng("wirklich")]),
            NewLine(),
            MultilineComment([NonEng('ц'), NonEng("blanco"), "<us_sep>", "english"]),
            NewLine(), Tab(),
            OneLineComment(['<capital>', NonEng("dieselbe"), '<cc_sep>', "8"])
        ]

        self.assertEqual(expected, actual)

    def test_to_repr_spl_1_numspl_1(self):
        prep_params = {PreprocessingType.SPL: True, PreprocessingType.NUM_SPL: True,
                       PreprocessingType.NO_NEWLINES_TABS: True}
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
            StringLiteral(['<capital>', 'a', '<cc_sep>', NonEng("wirklich")]),
            MultilineComment([NonEng('ц'), NonEng("blanco"), "<us_sep>", "english"]),
            OneLineComment(['<capital>', NonEng("dieselbe"), '<cc_sep>', "8"])
        ]

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
