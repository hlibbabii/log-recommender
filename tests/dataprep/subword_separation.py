import unittest

from logrec.dataprep.preprocess_params import pp_params
from logrec.dataprep.preprocessors import apply_preprocessors
from logrec.dataprep.preprocessors.general import from_string
from logrec.dataprep.preprocessors.model.containers import SplitContainer, StringLiteral
from logrec.dataprep.preprocessors.model.logging import LogStatement, INFO
from logrec.dataprep.preprocessors.model.noneng import NonEngSubWord, NonEngFullWord
from logrec.dataprep.preprocessors.model.numeric import Number, DecimalPoint, E
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.preprocessors.model.word import FullWord, SubWord, Capitalization, WordStart
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
        [placeholders["capital"], "vector"],
        [placeholders["capital"], "vector"]
    ),
    "players": (
        [FullWord.of("players")],
        ['play', placeholders["same_case_separator"], "er", placeholders["same_case_separator"], "s"],
        [placeholders["camel_case_separator"], 'play', 'er', 's', placeholders["split_words_end"]]
    ),
    "0.345e+4": (
        [Number(["0", DecimalPoint(), "3", "4", "5", E(), "+", "4"])],
        ["0.", placeholders["same_case_separator"], "3", placeholders["same_case_separator"], "4",
         placeholders["same_case_separator"], "5", placeholders["same_case_separator"], "e+",
         placeholders["same_case_separator"], "4"],
        [placeholders["camel_case_separator"], "0.", "3", "4", "5", "e+", "4", placeholders["split_words_end"]]
    ),
    "bestPlayers": (
        [SplitContainer([SubWord.of("best"), SubWord.of("Players")])],
        ["best", placeholders["camel_case_separator"], 'play', placeholders["same_case_separator"], "er",
         placeholders["same_case_separator"], "s"],
        [placeholders["camel_case_separator"], "best", placeholders["camel_case_separator"], 'play', "er", "s",
         placeholders["split_words_end"]]
    ),
    "test_BestPlayers": (
        [SplitContainer([SubWord.of("test"), SubWord.of("_Best"), SubWord.of("Players")])],
        ["test", placeholders["underscore_separator"], placeholders["capital"], "best",
         placeholders["camel_case_separator"], 'play', placeholders["same_case_separator"], "er",
         placeholders["same_case_separator"], "s"],
        [placeholders["camel_case_separator"], "test", placeholders["underscore_separator"], placeholders["capital"],
         "best", placeholders["camel_case_separator"], 'play', "er", "s", placeholders["split_words_end"]]
    ),
    "test_BestPlayers_modified": (
        [SplitContainer(
            [SubWord.of("test"), SubWord.of("_Best"), SubWord.of("Players"), SubWord.of("_modified")]
        )],
        ["test", placeholders["underscore_separator"], placeholders["capital"], "best",
         placeholders["camel_case_separator"], 'play', placeholders["same_case_separator"], "er",
         placeholders["same_case_separator"], "s", placeholders["underscore_separator"],
         "mod", placeholders["same_case_separator"], "if", placeholders["same_case_separator"], "ied"],
        [placeholders["camel_case_separator"], "test", placeholders["underscore_separator"], placeholders["capital"],
         "best", placeholders["camel_case_separator"], 'play', "er", "s", placeholders["underscore_separator"], "mod",
         "if", "ied",
         placeholders["split_words_end"]]
    ),
    "N_PLAYERS_NUM": (
        [SplitContainer([SubWord.of("N"), SubWord.of("_PLAYERS"), SubWord.of("_NUM")])],
        [placeholders["capital"], "n", placeholders["underscore_separator"], placeholders["capitals"], "play",
         placeholders["same_case_separator"], "er", placeholders["same_case_separator"], "s",
         placeholders["underscore_separator"], placeholders["capitals"], "num"],
        [placeholders["camel_case_separator"], placeholders["capital"], "n", placeholders["underscore_separator"],
         placeholders["capitals"], "play", "er", "s", placeholders["underscore_separator"], placeholders["capitals"],
         "num", placeholders["split_words_end"]]
    ),
    "test_очень": (
        [SplitContainer([SubWord.of("test"), NonEngSubWord(SubWord.of("_очень"))])],
        ["test", placeholders["underscore_separator"], placeholders['non_eng']],
        [placeholders["camel_case_separator"], "test", placeholders["underscore_separator"], placeholders['non_eng'],
         placeholders["split_words_end"]]
    ),
    "очень_test": (
        [SplitContainer([NonEngSubWord(SubWord("очень", Capitalization.NONE, WordStart())), SubWord.of("_test")])],
        [placeholders['non_eng'], placeholders["underscore_separator"], "test"],
        [placeholders["camel_case_separator"], placeholders['non_eng'], placeholders["underscore_separator"], "test",
         placeholders["split_words_end"]]
    ),
    "testWчень": (
        [SplitContainer([SubWord.of("test"), NonEngSubWord(SubWord.of("Wчень"))])],
        ["test", placeholders["camel_case_separator"], placeholders['non_eng']],
        [placeholders["camel_case_separator"], "test", placeholders["camel_case_separator"], placeholders['non_eng'],
         placeholders["split_words_end"]]
    ),
    "сегодня": (
        [NonEngFullWord(FullWord.of("сегодня"))],
        [placeholders['non_eng']],
        [placeholders['non_eng']]
    ),
    "_сегодня": (
        [NonEngFullWord(FullWord.of("_сегодня"))],
        [placeholders['underscore_separator'], placeholders['non_eng']],
        [placeholders['underscore_separator'], placeholders['non_eng']]
    ),
    "_Сегодня": (
        [NonEngFullWord(FullWord.of("_Сегодня"))],
        [placeholders['underscore_separator'], placeholders['capital'], placeholders['non_eng']],
        [placeholders['underscore_separator'], placeholders['capital'], placeholders['non_eng']]
    ),
    "Сегодня": (
        [NonEngFullWord(FullWord.of("Сегодня"))],
        [placeholders['capital'], placeholders['non_eng']],
        [placeholders['capital'], placeholders['non_eng']]
    ),
    '"сегодня"': (
        [StringLiteral([NonEngFullWord(FullWord.of("сегодня"))])],
        ['"', placeholders['non_eng'], '"'],
        ['"', placeholders['non_eng'], '"']
    ),
    'logger.info("Установлена licht4bild пользователем" + user.getNick()) ;': (
        [LogStatement(FullWord.of('logger'), FullWord.of('info'), INFO,
                      [StringLiteral([
                          NonEngFullWord(FullWord.of('Установлена')),
                          SplitContainer([
                              NonEngSubWord(SubWord('licht', Capitalization.NONE, WordStart())),
                              SubWord.of('4'),
                              NonEngSubWord(SubWord.of('bild'))
                          ]),
                          NonEngFullWord(FullWord.of('пользователем'))
                      ]), '+', FullWord.of('user'), '.',
                          SplitContainer([
                              SubWord.of('get'),
                              SubWord.of('Nick')
                          ]), '(', ')'])],
        ['`L', '`info', 'logger', '.', 'info', '(', '"', '`C', '`E', '`E', '`c', '4', '`c', '`E', '`E', '"',
         '+', 'user', '.', 'get', '`c', 'ni', '`s', 'ck', '(', ')', ')', 'L`', ';'],
        ['`L', '`info', 'logger', '.', 'info', '(', '"', '`C', '`E', '`c', '`E', '`c', '4', '`c', '`E', 'w`', '`E', '"',
         '+', 'user', '.', '`c', 'get', '`c', 'ni', 'ck', 'w`', '(', ')', ')', 'L`', ';']
    )
}

bpe_merges_cache = {
    "players": ["play", "er", "s"],
    "0.345e+4": ["0.", "3", "4", "5", "e+", "4"],
    "modified": ["mod", "if", "ied"],

    "create": ["create"],
    "vector": ["vector"],
    "best": ["best"],
    "test": ["test"],
    "num": ["num"],
    "user": ["user"],
    "get": ["get"],
    "nick": ["ni", "ck"],
    "logger": ["logger"],
    "info": ["info"]
}

prep_params_separators = {
    PreprocessingParam.EN_ONLY: 1,
    PreprocessingParam.NO_COM_STR: 0,
    PreprocessingParam.SPL: 4,
    PreprocessingParam.NO_SEP: 0,
    PreprocessingParam.NO_NEWLINES_TABS: 1,
}

prep_params_boundaries = {
    PreprocessingParam.EN_ONLY: 1,
    PreprocessingParam.NO_COM_STR: 0,
    PreprocessingParam.SPL: 4,
    PreprocessingParam.NO_SEP: 1,
    PreprocessingParam.NO_NEWLINES_TABS: 1,
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
