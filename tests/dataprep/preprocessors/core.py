import unittest

from logrec.dataprep.preprocessors.preprocessor_list import pp_params
from logrec.dataprep.preprocessors.core import apply_preprocessors
from logrec.dataprep.preprocessors.general import from_file
from logrec.dataprep.model.chars import NewLine, Tab, Backslash, Quote
from logrec.dataprep.model.containers import OneLineComment, SplitContainer, StringLiteral, \
    MultilineComment
from logrec.dataprep.model.noneng import NonEngSubWord
from logrec.dataprep.model.numeric import HexStart, Number, DecimalPoint, L, F, E, D
from logrec.dataprep.model.word import FullWord, SubWord

text2 = '''
_my_favoRite_ints_
'''

text3 = '''" RegisterImage "'''


# print(dd)

class ApplyPreprocessorsTest(unittest.TestCase):
    def __test_apply_preprocessors(self, input, expected):
        res = apply_preprocessors(from_file([l for l in input.split("\n")]), pp_params["preprocessors"], {
            'interesting_context_words': []})
        self.assertEqual(expected, res)

    def test_1(self):
        text = '''
long[] lovely_longs = {0x34a35EL,     0x88bc96fl           , -0x34L};
'''
        expected_result = [NewLine(),
                           FullWord.of('long'),
                           '[',
                           ']',
                           SplitContainer([SubWord.of('lovely'), SubWord.of('_longs')]),
                           '=',
                           '{',
                           Number([HexStart(), '3', '4', 'a', '3', '5', 'E', L()]),
                           ',',
                           Tab(),
                           Number([HexStart(), '8', '8', 'b', 'c', '9', '6', 'f', L()]),
                           Tab(),
                           Tab(),
                           ',',
                           Number(['-', HexStart(), '3', '4', L()]),
                           '}',
                           ';',
                           NewLine(), NewLine()]

        self.__test_apply_preprocessors(text, expected_result)

    def test_2(self):
        text = '''
int[] _my_favoRite_ints_ = {0x12, 0x1fE, 441, -81, -0xfFf};
'''
        expected_result = [NewLine(),
                           FullWord.of('int'),
                           '[',
                           ']',
                           SplitContainer(
                               [SubWord.of('my'), NonEngSubWord(SubWord.of('_favo')),
                                SubWord.of('Rite'), SubWord.of('_ints'), SubWord.of("_")]
                           ),
                           '=',
                           '{',
                           Number([HexStart(), '1', '2']),
                           ',',
                           Number([HexStart(), '1', 'f', 'E']),
                           ',',
                           Number(['4', '4', '1']),
                           ',',
                           Number(['-', '8', '1']),
                           ',',
                           Number(['-', HexStart(), 'f', 'F', 'f']),
                           '}',
                           ';',
                           NewLine(), NewLine()]

        self.__test_apply_preprocessors(text, expected_result)

    def test_3(self):
        text = '''
float[] floats = {-0.43E4f, .58F, 0.d, -9.63e+2D, 0.E-8};
'''
        expected_result = [NewLine(),
                           FullWord.of('float'),
                           '[',
                           ']',
                           FullWord.of('floats'),
                           '=',
                           '{',
                           Number(['-', '0', DecimalPoint(), '4', '3', E(), '4', F()]),
                           ',',
                           Number([DecimalPoint(), '5', '8', F()]),
                           ',',
                           Number(['0', DecimalPoint(), D()]),
                           ',',
                           Number(['-', '9', DecimalPoint(), '6', '3', E(), '+', '2', D()]),
                           ',',
                           Number(['0', DecimalPoint(), E(), '-', '8']),
                           '}',
                           ';',
                           NewLine(), NewLine()]

        self.__test_apply_preprocessors(text, expected_result)

    def test_4(self):
        text = '''
BigAWESOMEString[] a2y = "abc".doSplit("\\"");
'''
        expected_result = [NewLine(), SplitContainer(
            [SubWord.of('Big'), SubWord.of('AWESOME'), SubWord.of('String')]),
                           '[',
                           ']',
                           SplitContainer([SubWord.of('a'), SubWord.of('2'), SubWord.of('y')]),
                           '=',
                           StringLiteral([FullWord.of('abc')]),
                           '.',
                           SplitContainer([SubWord.of('do'), SubWord.of('Split')]),
                           '(',
                           StringLiteral([Backslash(), Quote()]),
                           ')',
                           ';',
                           NewLine(), NewLine()]

        self.__test_apply_preprocessors(text, expected_result)

    def test_5(self):
        text = '''
// this code won't compile but the preprocessing still has to be done corrrectly
'''
        expected_result = [NewLine(), OneLineComment([FullWord.of('this'), FullWord.of('code'),
                                                      FullWord.of('won'), "'", FullWord.of('t'),
                                                      FullWord.of('compile'), FullWord.of('but'),
                                                      FullWord.of('the'), FullWord.of('preprocessing'),
                                                      FullWord.of('still'), FullWord.of('has'),
                                                      FullWord.of('to'), FullWord.of('be'),
                                                      FullWord.of('done'), FullWord.of('corrrectly')]),
                           NewLine(), NewLine()]

        self.__test_apply_preprocessors(text, expected_result)

    def test_6(self):
        text = '''
9a abc1
~-0xFFFFFL=
.0E+5
|=
?
==
!=
**
++
--
+=
-=
/=
*=
%=
$
<=
>=
@
    ^=
    &=
    #
                                                                                 >>
<<
&&
||
+*!/><\t\n
{}[],.-:();&|\\'~%^
'''

        expected_result = [NewLine(),
                           SplitContainer([SubWord.of('9'), SubWord.of('a')]),
                           SplitContainer([SubWord.of('abc'), SubWord.of('1')]),
                           NewLine(),
                           '~',
                           Number(['-', HexStart(), 'F', 'F', 'F', 'F', 'F', L()]),
                           '=',
                           NewLine(),
                           Number([DecimalPoint(), '0', E(), '+', '5']),
                           NewLine(),
                           '|=',
                           NewLine(),
                           '?',
                           NewLine(),
                           '==',
                           NewLine(),
                           '!=',
                           NewLine(),
                           '**',
                           NewLine(),
                           '++',
                           NewLine(),
                           '--',
                           NewLine(),
                           '+=',
                           NewLine(),
                           '-=',
                           NewLine(),
                           '/=',
                           NewLine(),
                           '*=',
                           NewLine(),
                           '%=',
                           NewLine(),
                           '$',
                           NewLine(),
                           '<=',
                           NewLine(),
                           '>=',
                           NewLine(),
                           '@',
                           NewLine(),
                           Tab(),
                           '^=',
                           NewLine(),
                           Tab(),
                           '&=',
                           NewLine(),
                           Tab(),
                           '#',
                           NewLine(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           Tab(),
                           '>>',
                           NewLine(),
                           '<<',
                           NewLine(),
                           '&&',
                           NewLine(),
                           '||',
                           NewLine(),
                           '+',
                           '*',
                           '!',
                           '/',
                           '>',
                           '<',
                           Tab(),
                           NewLine(),
                           NewLine(),
                           '{',
                           '}',
                           '[',
                           ']',
                           ',',
                           '.',
                           '-',
                           ':',
                           '(',
                           ')',
                           ';',
                           '&',
                           '|',
                           Backslash(),
                           "'",
                           '~',
                           '%',
                           '^',
                           NewLine(), NewLine()]

        self.__test_apply_preprocessors(text, expected_result)

    def test_7(self):
        text = '''
/*multi-line MyComment_
*//
_operations
'''

        expected_result = [NewLine(),
                           MultilineComment([FullWord.of('multi'), '-', FullWord.of('line'),
                                             SplitContainer([
                                                 SubWord.of('My'),
                                                 SubWord.of('Comment'),
                                                 SubWord.of('_')
                                             ]),
                                             NewLine()]),
                           '/',
                           NewLine(),
                           FullWord.of('_operations'),
                           NewLine(),
                           NewLine()]

        self.__test_apply_preprocessors(text, expected_result)

    def test_capitals(self):
        text = '''
MyClass Class CONSTANT VAR_WITH_UNDERSCORES
'''

        expected_result = [NewLine(),
                           SplitContainer([SubWord.of("My"), SubWord.of("Class")]),
                           FullWord.of("Class"), FullWord.of("CONSTANT"),
                           SplitContainer([SubWord.of("VAR"),
                                           SubWord.of("_WITH"),
                                           SubWord.of("_UNDERSCORES")]),
                           NewLine(), NewLine()]

        self.__test_apply_preprocessors(text, expected_result)


if __name__ == '__main__':
    unittest.main()
