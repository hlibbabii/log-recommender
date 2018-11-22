import unittest

from logrec.dataprep.preprocessors.general import spl_verbose
from logrec.dataprep.preprocessors.model.capitals import Capitals
from logrec.dataprep.preprocessors.model.chars import MultilineCommentStart, MultilineCommentEnd, OneLineCommentStart, \
    Quote, \
    Backslash, Tab
from logrec.dataprep.preprocessors.model.general import ProcessableToken


class GeneralTest(unittest.TestCase):
    def test_split_verbose1(self):
        text = '''
long[] lovely_longs = {/* there should be some longs here*/};
int[] _my_favoRite_ints_ = {/* ints here*/};
'''
        actual = spl_verbose([ProcessableToken(text)], None)

        expected = ['\n', ProcessableToken("long"), '[', ']', ProcessableToken("lovely_longs"),
                    '=', '{', MultilineCommentStart(), ProcessableToken("there"), ProcessableToken("should"),
                    ProcessableToken("be"), ProcessableToken("some"), ProcessableToken("longs"),
                    ProcessableToken("here"), MultilineCommentEnd(), "}", ';', '\n', ProcessableToken("int"),
                    '[', ']', ProcessableToken("_my_favoRite_ints_"), '=', '{', MultilineCommentStart(),
                    ProcessableToken("ints"), ProcessableToken("here"), MultilineCommentEnd(), '}', ';', '\n',
                    ]

        self.assertEqual(expected, actual)

    def test_split_verbose2(self):
        text='''
float[] floats = {}; //floats were removed 
BigAWESOMEString[] a2y = "abc".doSplit("\\"");
'''
        actual = spl_verbose([ProcessableToken(text)], None)

        expected = ['\n', ProcessableToken("float"), '[', ']', ProcessableToken("floats"), '=', '{', '}',
                    ';', OneLineCommentStart(), ProcessableToken("floats"), ProcessableToken("were"),
                    ProcessableToken("removed"), '\n', ProcessableToken("BigAWESOMEString"),
                    '[', ']', ProcessableToken("a2y"), '=', Quote(), ProcessableToken("abc"), Quote(), '.',
                    ProcessableToken("doSplit"), '(', Quote(), Backslash(), Quote(), Quote(), ')', ';', '\n', ]

        self.assertEqual(expected, actual)

    def test_split_verbose3(self):
        text = '''
// this code won't compile but the preprocessing still has to be done corrrectly
9a ** abc1
~-|=?==!=/* gj **/
'''
        actual = spl_verbose([ProcessableToken(text)], None)

        expected = ['\n',OneLineCommentStart(),
                    ProcessableToken("this"), ProcessableToken("code"), ProcessableToken("won"),
                    "'", ProcessableToken("t"), ProcessableToken("compile"), ProcessableToken("but"),
                    ProcessableToken("the"), ProcessableToken("preprocessing"), ProcessableToken("still"),
                    ProcessableToken("has"), ProcessableToken("to"), ProcessableToken("be"),
                    ProcessableToken("done"), ProcessableToken("corrrectly"), '\n',
                    ProcessableToken("9a"), '**', ProcessableToken("abc1"), '\n', '~', '-', '|=', '?',
                    '==', '!=', MultilineCommentStart(), ProcessableToken("gj"), '*',
                    MultilineCommentEnd(), '\n']

        self.assertEqual(expected, actual)

    def test_split_verbose4(self):
        text = '''
a++a
b--b
c+=c
d-=d
e/=e
f*=f
g%=g
h$h
i<=i
j>=j
k@k
    l^=l
    m&=m
    n#n
                                                                    o>>o
p<<p
q&&q
r||r
+*!/><\t\n
{}[],.-:();&|\\'~%^
/*multi-line MyComment_
*//
_operations
'''
        actual = spl_verbose([ProcessableToken(text)], None)

        expected = ['\n', ProcessableToken('a'), '++', ProcessableToken('a'),
                    '\n', ProcessableToken('b'), '--', ProcessableToken('b'),
                    '\n', ProcessableToken('c'), '+=', ProcessableToken('c'),
                    '\n', ProcessableToken('d'), '-=', ProcessableToken('d'),
                    '\n', ProcessableToken('e'), '/=', ProcessableToken('e'),
                    '\n', ProcessableToken('f'), '*=', ProcessableToken('f'),
                    '\n', ProcessableToken('g'), '%=', ProcessableToken('g'),
                    '\n', ProcessableToken('h'), '$', ProcessableToken('h'),
                    '\n', ProcessableToken('i'), '<=', ProcessableToken('i'),
                    '\n', ProcessableToken('j'), '>=', ProcessableToken('j'),
                    '\n', ProcessableToken('k'), '@', ProcessableToken('k'),
                    '\n', ProcessableToken('l'), '^=', ProcessableToken('l'),
                    '\n', ProcessableToken('m'), '&=', ProcessableToken('m'),
                    '\n', ProcessableToken('n'), '#', ProcessableToken('n'),
                    '\n', ProcessableToken('o'), '>>', ProcessableToken('o'),
                    '\n', ProcessableToken('p'), '<<', ProcessableToken('p'),
                    '\n', ProcessableToken('q'), '&&', ProcessableToken('q'),
                    '\n', ProcessableToken('r'), '||', ProcessableToken('r'),
                    '\n', '+', '*', '!', '/', '>', '<', Tab(), '\n', '\n', '{', '}', '[',
                    ']', ',', '.', '-', ':', '(', ')', ';', '&', '|', Backslash(), "'", '~', '%', '^',
                    '\n', MultilineCommentStart(), ProcessableToken("multi"), '-', ProcessableToken("line"),
                    ProcessableToken("MyComment_"), '\n', MultilineCommentEnd(), '/', '\n',
                    ProcessableToken("_operations"), '\n']

        self.assertEqual(expected, actual)

    def test_split_verbose_log_statement(self):
        text = '''
logger.info("The value is " + val);
'''
        actual = spl_verbose([ProcessableToken(text)], None)

        expected = ['\n', ProcessableToken("logger"), '.', ProcessableToken("info"),
                    '(', Quote(), ProcessableToken("The"), ProcessableToken("value"), ProcessableToken("is"), Quote(),
                    '+', ProcessableToken('val'), ')', ';', '\n',
                    ]

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
