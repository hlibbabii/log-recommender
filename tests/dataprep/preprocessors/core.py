import unittest

from logrec.dataprep.preprocess_params import pp_params
from logrec.dataprep.preprocessors.core import apply_preprocessors
from logrec.dataprep.preprocessors.model.chars import NewLine, Tab, Backslash, Quote
from logrec.dataprep.preprocessors.model.general import ProcessableToken, NonEng
from logrec.dataprep.preprocessors.model.numeric import HexStart, Number, DecimalPoint, L, F, E, D
from logrec.dataprep.preprocessors.model.split import UnderscoreSplit, CamelCaseSplit, WithNumbersSplit
from logrec.dataprep.preprocessors.model.textcontainers import OneLineComment, StringLiteral, MultilineComment

text2 = '''
_my_favoRite_ints_
'''

text3 = '''" RegisterImage "'''


# print(dd)

class ApplyPreprocessorsTest(unittest.TestCase):
    def __test_apply_preprocessors(self, input, expected):
        res = apply_preprocessors([l for l in input.split("\n")], pp_params["preprocessors"], {
            'interesting_context_words': []})
        self.assertEqual(expected, res)

    def test_1(self):
        text = '''
long[] lovely_longs = {0x34a35EL,     0x88bc96fl           , -0x34L};
'''
        expected_result = [NewLine(),
                           ProcessableToken('long'),
                           '[',
                           ']',
                           UnderscoreSplit([ProcessableToken('lovely'), ProcessableToken('longs')]),
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
                           ProcessableToken('int'),
                           '[',
                           ']',
                           CamelCaseSplit([UnderscoreSplit(
                               [ProcessableToken(""), ProcessableToken('my'), NonEng(ProcessableToken('favo'))]),
                                           UnderscoreSplit([ProcessableToken('rite'), ProcessableToken('ints'),
                                                            ProcessableToken("")])], False),
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
                           ProcessableToken('float'),
                           '[',
                           ']',
                           ProcessableToken('floats'),
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
        expected_result = [NewLine(), CamelCaseSplit(
            [ProcessableToken('big'), ProcessableToken('awesome'), ProcessableToken('string')], True),
                           '[',
                           ']',
                           WithNumbersSplit([ProcessableToken('a'), ProcessableToken('2'), ProcessableToken('y')],
                                            False),
                           '=',
                           StringLiteral([ProcessableToken('abc')]),
                           '.',
                           CamelCaseSplit([ProcessableToken('do'), ProcessableToken('split')], False),
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
        expected_result = [NewLine(), OneLineComment([ProcessableToken('this'), ProcessableToken('code'),
                                                      ProcessableToken('won'), "'", ProcessableToken('t'),
                                                      ProcessableToken('compile'), ProcessableToken('but'),
                                                      ProcessableToken('the'), ProcessableToken('preprocessing'),
                                                      ProcessableToken('still'), ProcessableToken('has'),
                                                      ProcessableToken('to'), ProcessableToken('be'),
                                                      ProcessableToken('done'), ProcessableToken('corrrectly')]),
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
                           WithNumbersSplit([ProcessableToken('9'), ProcessableToken('a')], False),
                           WithNumbersSplit([ProcessableToken('abc'), ProcessableToken('1')], False),
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
                           MultilineComment([ProcessableToken('multi'), '-', ProcessableToken('line'),
                                             CamelCaseSplit([ProcessableToken('my'),
                                                             UnderscoreSplit([ProcessableToken('comment'),
                                                                              ProcessableToken('')])], True),
                                             NewLine()]),
                           '/',
                           NewLine(),
                           UnderscoreSplit([ProcessableToken(''), ProcessableToken('operations')]),
                           NewLine(),
                           NewLine()]

        self.__test_apply_preprocessors(text, expected_result)


if __name__ == '__main__':
    unittest.main()
