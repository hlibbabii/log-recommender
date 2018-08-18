import deepdiff

from dataprep.preprocessors.core import apply_preprocessors
from nn.preprocess_params import pp_params

text2 = '''
] _my_favorite_ints_
'''

text = '''
long[] lovely_longs = {0x34a35EL,     0x88bc96fl           , -0x34L};
int[] _my_favorite_ints_ = {0x12, 0x1fE, 441, -81, -0xfFf};
float[] floats = {-0.43E4f, .58F, 0.d, -9.63e+2D, 0.E-8}; 
BigAWESOMEString[] a2y = "abc".doSplit("\\"");
// this code won't compile but the preprocessing still has to be done corrrectly
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
/*multi-line comment
*/

'''

res = apply_preprocessors([l for l in text.split("\n")], pp_params["preprocessors"], {
    'interesting_context_words': []})

print(res)

expected_result = ['long', '[', ']', 'lovely', '`ussep`', 'longs', '=', '{', '`hexstart`', '3', '4', 'a',
                   '3', '5', 'e', '`lng`', ',', '`hexstart`', '8', '8', 'b', 'c', '9', '6', 'f', '`lng`',
                   ',', '-', '`hexstart`', '3', '4', '`lng`', '}', ';', 'int', '[', ']', '`ussep`', 'my',
                   '`ussep`', 'favorite', '`ussep`', 'ints', '`ussep`', '=', '{', '`hexstart`', '1', '2',
                   ',', '`hexstart`', '1', 'f', 'e', ',', '4', '4', '1', ',', '-', '8', '1', ',', '-',
                   '`hexstart`', 'f', 'f', 'f', '}', ';', 'float', '[', ']', 'floats', '=', '{', '-',
                   '0', '`dot`', '4', '3', '`e`', '4', '`flt`', ',', '`dot`', '5', '8', '`flt`', ',',
                   '0', '`dot`', '`double`', ',', '-', '9', '`dot`', '6', '3', '`e`', '+', '2',
                   '`double`', ',', '0', '`dot`', '`e`', '-', '8', '}', ';', 'big', '`ccsep`',
                   'awesome', '`ccsep`', 'string', '[', ']', 'a', '`ccsep`', '2', '`ccsep`', 'y',
                   '=', '`stringliteral`', '.', 'do', '`ccsep`', 'split', '(', '`stringliteral`', ')',
                   ';', '`comment`', '9', '`ccsep`', 'a', 'abc', '`ccsep`', '1', '~', '-', '`hexstart`', 'f', 'f', 'f',
                   'f', 'f', '`lng`', '=', '`dot`', '0', '`e`', '+', '5', '|=', '?', '==', '!=', '**',
                   '++', '--', '+=', '-=', '/=', '*=', '%=', '$', '<=', '>=', '@', '^=', '&=', '#', '>>',
                   '<<', '&&', '||', '+', '*', '!', '/', '>', '<', '{', '}', '[', ']', ',', '.', '-', ':',
                   '(', ')', ';', '&', '|', '\\', "'", '~', '%', '^', '`comment`']

dd = deepdiff.DeepDiff(expected_result, res)
print(dd)
