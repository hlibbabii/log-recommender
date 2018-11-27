import unittest

from logrec.dataprep.preprocess_params import pp_params
from logrec.dataprep.preprocessors import apply_preprocessors
from logrec.dataprep.preprocessors.general import from_string
from logrec.dataprep.preprocessors.model.containers import SplitContainer
from logrec.dataprep.preprocessors.model.numeric import Number, DecimalPoint, E
from logrec.dataprep.preprocessors.model.word import FullWord, SubWord
from logrec.dataprep.preprocessors.preprocessing_types import PreprocessingParam
from logrec.dataprep.split.ngram import NgramSplitConfig, NgramSplittingType
from logrec.dataprep.to_repr import to_repr

test_cases = {
    "create": (
        [FullWord.of("create")],
        ["create"],
        ["create"]
    ),
    "Vector": (
        [FullWord.of("Vector")],
        ['`C', "vector"],
        ['`C', "vector"]
    ),
    "players": (
        [FullWord.of("players")],
        ['play', "<sc_sep>", "er", "<sc_sep>", "s"],
        ['<cc_sep>', 'play', 'er', 's', 's`']
    ),
    "0.345e+4": (
        [Number(["0", DecimalPoint(), "3", "4", "5", E(), "+", "4"])],
        ["0.", "<sc_sep>", "3", "<sc_sep>", "4", "<sc_sep>", "5", "<sc_sep>", "e+", "<sc_sep>", "4"],
        ["<cc_sep>", "0.", "3", "4", "5", "e+", "4", 's`']
    ),
    "bestPlayers": (
        [SplitContainer([SubWord.of("best"), SubWord.of("Players")])],
        ["best", "<cc_sep>", 'play', "<sc_sep>", "er", "<sc_sep>", "s"],
        ["<cc_sep>", "best", "<cc_sep>", 'play', "er", "s", "s`"]
    ),
    "test_BestPlayers": (
        [SplitContainer([SubWord.of("test"), SubWord.of("_Best"), SubWord.of("Players")])],
        ["test", "<us_sep>", "`C", "best", "<cc_sep>", 'play', "<sc_sep>", "er", "<sc_sep>", "s"],
        ["<cc_sep>", "test", "<us_sep>", "`C", "best", "<cc_sep>", 'play', "er", "s", "s`"]
    ),
    "test_BestPlayers_modified": (
        [SplitContainer(
            [SubWord.of("test"), SubWord.of("_Best"), SubWord.of("Players"), SubWord.of("_modified")]
        )],
        ["test", "<us_sep>", "`C", "best", "<cc_sep>", 'play', "<sc_sep>", "er", "<sc_sep>", "s", "<us_sep>",
         "mod", "<sc_sep>", "if", "<sc_sep>", "ied"],
        ["<cc_sep>", "test", "<us_sep>", "`C", "best", "<cc_sep>", 'play', "er", "s", "<us_sep>", "mod", "if", "ied",
         's`']
    ),
    "N_PLAYERS_NUM": (
        [SplitContainer([SubWord.of("N"), SubWord.of("_PLAYERS"), SubWord.of("_NUM")])],
        ["`C", "n", "<us_sep>", "`Cs", "play", "<sc_sep>", "er", "<sc_sep>", "s", "<us_sep>", "`Cs", "num"],
        ["<cc_sep>", "`C", "n", "<us_sep>", "`Cs", "play", "er", "s", "<us_sep>", "`Cs", "num", 's`']
    ),
}

bpe_merges_cache = {
    "players": ["play", "er", "s"],
    "0.345e+4": ["0.", "3", "4", "5", "e+", "4"],
    "modified": ["mod", "if", "ied"],

    "create": ["create"],
    "vector": ["vector"],
    "best": ["best"],
    "test": ["test"],
    "num": ["num"]
}

prep_params_separators = {
    PreprocessingParam.EN_ONLY: 1,
    PreprocessingParam.NO_COM_STR: 0,
    PreprocessingParam.SPL: 4,
    PreprocessingParam.NO_SEP: 0,
    PreprocessingParam.NO_NEWLINES_TABS: 1,
    PreprocessingParam.NO_LOGS: 0
}

prep_params_boundaries = {
    PreprocessingParam.EN_ONLY: 1,
    PreprocessingParam.NO_COM_STR: 0,
    PreprocessingParam.SPL: 4,
    PreprocessingParam.NO_SEP: 1,
    PreprocessingParam.NO_NEWLINES_TABS: 1,
    PreprocessingParam.NO_LOGS: 0
}

ngram_split_config = NgramSplitConfig(NgramSplittingType.BPE, merges_cache=bpe_merges_cache, merges={})


class SubwordSeparation(unittest.TestCase):
    def test(self):
        for input, output_tuple in test_cases.items():
            parsed = apply_preprocessors(from_string(input), pp_params["preprocessors"], {})

            self.assertEqual(output_tuple[0], parsed)

            repred = to_repr(prep_params_separators, parsed, ngram_split_config)

            self.assertEqual(output_tuple[1], repred)

            repred2 = to_repr(prep_params_boundaries, parsed, ngram_split_config)

            self.assertEqual(output_tuple[2], repred2)


if __name__ == '__main__':
    unittest.main()
