import unittest

from logrec.dataprep.model.noneng import NonEng
from logrec.dataprep.preprocessors.preprocessor_list import pp_params
from logrec.dataprep.preprocessors import apply_preprocessors
from logrec.dataprep.preprocessors.general import from_string
from logrec.dataprep.model.containers import SplitContainer, StringLiteral
from logrec.dataprep.model.logging import LogStatement, INFO
from logrec.dataprep.model.numeric import Number, DecimalPoint, E
from logrec.dataprep.model.placeholders import placeholders
from logrec.dataprep.model.word import Word, Underscore
from logrec.dataprep.prepconfig import PrepConfig
from logrec.dataprep.split.ngram import NgramSplitConfig, NgramSplittingType
from logrec.dataprep.to_repr import to_repr

test_cases = {
    "create": (
        [SplitContainer.from_single_token("create")],
        ["create"],
    ),
    "Vector": (
        [SplitContainer.from_single_token("Vector")],
        [placeholders["capital"], "vector"],
    ),
    "players": (
        [SplitContainer.from_single_token("players")],
        [placeholders["word_start"], 'play', 'er', 's', placeholders["word_end"]]
    ),
    "0.345e+4": (
        [Number(["0", DecimalPoint(), "3", "4", "5", E(), "+", "4"])],
        [placeholders["word_start"], "0.", "3", "4", "5", "e+", "4", placeholders["word_end"]]
    ),
    "bestPlayers": (
        [SplitContainer([Word.from_("best"), Word.from_("Players")])],
        [placeholders["word_start"], "best", placeholders["capital"], 'play', "er", "s", placeholders["word_end"]]
    ),
    "test_BestPlayers": (
        [SplitContainer([Word.from_("test"), Underscore(), Word.from_("Best"), Word.from_("Players")])],
        [placeholders["word_start"], "test", '_', placeholders["capital"],
         "best", placeholders["capital"], 'play', "er", "s", placeholders["word_end"]]
    ),
    "test_BestPlayers_modified": (
        [SplitContainer(
            [Word.from_("test"), Underscore(), Word.from_("Best"), Word.from_("Players"), Underscore(),
             Word.from_("modified")]
        )],
        [placeholders["word_start"], "test", '_', placeholders["capital"],
         "best", placeholders["capital"], 'play', "er", "s", '_', "mod",
         "if", "ied",
         placeholders["word_end"]]
    ),
    "N_PLAYERS_NUM": (
        [SplitContainer([Word.from_("N"), Underscore(), Word.from_("PLAYERS"), Underscore(), Word.from_("NUM")])],
        [placeholders["word_start"], placeholders["capitals"], "n", '_',
         placeholders["capitals"], "play", "er", "s", '_', placeholders["capitals"],
         "num", placeholders["word_end"]]
    ),
    "test_очень": (
        [SplitContainer([Word.from_("test"), Underscore(), NonEng(Word.from_("очень"))])],
        [placeholders["word_start"], "test", '_', placeholders['non_eng'], placeholders["word_end"]]
    ),
    "очень_test": (
        [SplitContainer([NonEng(Word.from_("очень")), Underscore(), Word.from_("test")])],
        [placeholders["word_start"], placeholders['non_eng'], '_', "test",
         placeholders["word_end"]]
    ),
    "testWчень": (
        [SplitContainer([Word.from_("test"), NonEng(Word.from_("Wчень"))])],
        [placeholders["word_start"], "test", placeholders['capital'], placeholders['non_eng'], placeholders["word_end"]]
    ),
    "сегодня": (
        [SplitContainer([(NonEng(Word.from_("сегодня")))])],
        [placeholders['non_eng']]
    ),
    "_сегодня": (
        [SplitContainer([Underscore(), (NonEng(Word.from_("сегодня")))])],
        [placeholders['word_start'], '_', placeholders['non_eng'], placeholders['word_end']]
    ),
    "_Сегодня": (
        [SplitContainer([Underscore(), (NonEng(Word.from_("Сегодня")))])],
        [placeholders['word_start'], '_', placeholders['capital'], placeholders['non_eng'], placeholders['word_end']]
    ),
    "Сегодня": (
        [SplitContainer([(NonEng(Word.from_("Сегодня")))])],
        [placeholders['capital'], placeholders['non_eng']]
    ),
    '"сегодня"': (
        [StringLiteral([SplitContainer([(NonEng(Word.from_("сегодня")))])])],
        ['"', placeholders['non_eng'], '"']
    ),
    'logger.info("Установлена licht4bild пользователем" + user.getNick()) ;': (
        [LogStatement(SplitContainer.from_single_token('logger'), SplitContainer.from_single_token('info'), INFO,
                      [StringLiteral([
                          SplitContainer([NonEng(Word.from_('Установлена'))]),
                          SplitContainer([
                              NonEng(Word.from_('licht')),
                              Word.from_('4'),
                              NonEng(Word.from_('bild'))
                          ]),
                          SplitContainer([NonEng(Word.from_('пользователем'))])
                      ]), '+', SplitContainer.from_single_token('user'), '.',
                          SplitContainer([
                              Word.from_('get'),
                              Word.from_('Nick')
                          ]), '(', ')'])],
        ['`L', '`info', 'logger', '.', 'info', '(', '"', '`C', '`E', '`w', '`E', '4', '`E', 'w`', '`E', '"',
         '+', 'user', '.', '`w', 'get', '`C', 'ni', 'ck', 'w`', '(', ')', ')', ';', 'L`']
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

ngram_split_config = NgramSplitConfig(NgramSplittingType.BPE, merges_cache=bpe_merges_cache, merges={})


class SubwordSeparation(unittest.TestCase):
    def test(self):
        for input, output_tuple in test_cases.items():
            parsed = apply_preprocessors(from_string(input), pp_params["preprocessors"], {})

            self.assertEqual(output_tuple[0], parsed)

            repred = to_repr(PrepConfig.from_encoded_string('104111'), parsed, ngram_split_config)

            self.assertEqual(output_tuple[1], repred)


if __name__ == '__main__':
    unittest.main()
