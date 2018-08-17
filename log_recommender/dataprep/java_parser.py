import re
import sys

START_MULTILINE_COMMENT = "/*"
END_MULTILINE_COMMENT = "*/"

START_ONE_LINE_COMMENT = "//"
EOF = "\n"

placeholders= {
    'comment': '`comment`',
    'string_literal': '`stringliteral`',
    'hex_start': '`hexstart`',
    'identifier': '`identifier`',
    'number_separator': '`numsep`',
    'same_case_separator': '`scsep`',
    'camel_case_separator': '`ccsep`',
    'underscore_separator': '`ussep`',
    'dot': '`dot`',
    'long': '`lng`',
    'float': '`flt`',
    'double': '`double`',
    'e': '`e`'
}

tabs = ["\t" + str(i) for i in range(11)]

two_character_tokens = [
    "/*",
    "*/",
    "==",
    "!=",
    "**",
    "//",
    "++",
    "--",
    "+=",
    "-=",
    "/=",
    "*=",
    "%=",
    "<=",
    ">=",
    "^=",
    "&=",
    "|=",
    ">>",
    "<<",
    "&&",
    "||"
]

one_character_tokens = [
    "+",
    "*",
    "!",
    "/",
    ">",
    "<",
    "="
]

two_char_verbose = [
    "\t", "\n"
]

one_char_verbose = [
    "{", "}", "[", "]", ",", ".", "-", "?", ":", "(", ")", ";", '"', "&",
    "|", "\\", "@", "#", "$", "'", "~", "%", "^", "\\"
]

delimiters_to_drop = "[\[\] ,.\-?:\n\t(){};\"&|_#\\\@$]"
delimiters_to_drop_verbose = " "

key_words = [
"abstract",
"continue",
"for",
"new",
"switch",
"assert",
"default",
"package",
"synchronized",
"boolean",
"do",
"if",
"private",
"this",
"break",
"double",
"implements",
"protected",
"throw",
"byte",
"else",
"import",
"public",
"throws",
"case",
"enum",
"instanceof",
"return",
"transient",
"catch",
"extends",
"int",
"short",
"try",
"char",
"final",
"interface",
"static",
"void",
"class",
"finally",
"long",
"strictfp",
"volatile",
"float",
"native",
"super",
"while",
"true",
"false",
"null"
]

NUMBER_REGEX = '-?(?:0x[0-9a-fA-F]+[lL]?|[0-9]+[lL]?|(?:[0-9]*\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?[fFdD]?)'


def is_number(s):
    return re.fullmatch(NUMBER_REGEX, s)


class JavaParser(object):
    def strip_off_multiline_comments(self, context):
        while True:
            try:
                start = context.index(START_MULTILINE_COMMENT)
            except ValueError:
                start = None
            try:
                end = context.index(END_MULTILINE_COMMENT)
            except ValueError:
                end = None

            if start is None and end is None:
                return context
            elif end is None:
                del(context[start:])
                context.append(placeholders['comment'])
            elif start is None or end < start:
                del(context[:end+1])
                context.insert(0, placeholders['comment'])
            elif start < end:
                del(context[start:end+1])
                context.insert(start, placeholders['comment'])

    def strip_off_one_line_comments(self, context):
        while True:
            try:
                start = context.index(START_ONE_LINE_COMMENT)
            except ValueError:
                return context

            try:
                eof_index = context[start+1:].index(EOF)
            except ValueError:
                eof_index = sys.maxsize
            abs_eof_index = start+eof_index+1
            del(context[start:abs_eof_index])
            context.insert(start, placeholders['comment'])

    def find_not_escaped_double_quote(self, str):
        index_to_start_search = 0
        while True:
            try:
                ind = str[index_to_start_search:].index('"')
                i = ind-1
                while i >= 0 and str[index_to_start_search+i] == "\\":
                    i -= 1
                if (ind - i) % 2 == 1:
                    return index_to_start_search + ind
                else:
                    index_to_start_search = index_to_start_search + ind + 1
            except ValueError:
                return None

    def strip_off_string_literals(self, context):
        while True:
            opening_quote_index = self.find_not_escaped_double_quote(context)
            if opening_quote_index is None:
                return context
            closing_quote_index = self.find_not_escaped_double_quote(context[opening_quote_index + 1:])
            if closing_quote_index is None:
                print(f'Warning: closing bracket is not found: {context[opening_quote_index + 1:]}')
                closing_quote_index = sys.maxsize
            abs_closing_quote_index = opening_quote_index + 1 + closing_quote_index
            del(context[opening_quote_index: abs_closing_quote_index+1])
            context.insert(opening_quote_index, placeholders['string_literal'])

    def strip_off_identifiers(self, identifiers_to_ignore, context):
        non_identifiers = set(key_words + two_character_tokens + one_character_tokens + one_char_verbose + two_char_verbose + \
                          list(placeholders.values()) + tabs + identifiers_to_ignore)

        result = []
        for word in context:
            if not is_number(word) and word not in non_identifiers:
                result.append(placeholders['identifier'])
            else:
                result.append(word)
        return result

    def process_number_literals(self, context):
        result = []
        for word in context:
            hex=False
            if is_number(word) and word not in tabs:
                if word.startswith('-'):
                    result.append('-')
                    word=word[1:]
                if word.startswith("0x"):
                    result.append(placeholders['hex_start'])
                    word=word[2:]
                    hex=True
                for ch in word:
                    if ch == '.':
                        result.append(placeholders['dot'])
                    elif ch == 'l' or ch == 'L':
                        result.append(placeholders['long'])
                    elif (ch == 'f' or ch == 'F') and not hex:
                        result.append(placeholders['float'])
                    elif (ch == 'd' or ch == 'D') and not hex:
                        result.append(placeholders['double'])
                    elif (ch == 'e' or ch == 'E') and not hex:
                        result.append(placeholders['e'])
                    else:
                        result.append(ch)
            else:
                result.append(word)
        return result