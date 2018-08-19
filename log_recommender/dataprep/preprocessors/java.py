import logging
import re
import sys

from dataprep.preprocessors.model.chars import MultilineCommentStart, MultilineCommentEnd, OneLineCommentStart, NewLine, \
    Backslash, Quote
from dataprep.preprocessors.model.general import ProcessableToken, ProcessableTokenContainer
from dataprep.preprocessors.model.numeric import Number, D, F, L, DecimalPoint, HexStart, E
from dataprep.preprocessors.model.placeholders import placeholders
from dataprep.preprocessors.model.textcontainers import MultilineComment, StringLiteral, OneLineComment

START_MULTILINE_COMMENT = MultilineCommentStart()
END_MULTILINE_COMMENT = MultilineCommentEnd()

START_ONE_LINE_COMMENT = OneLineCommentStart()
NEW_LINE = NewLine()

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
delimiters_to_drop_verbose = " " #TODO according to the new philosophy we shoulnt drop anything

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


def strip_off_multiline_comments(context):
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
            comment_content = context[start+1:]
            del (context[start:])
        elif start is None or end < start:
            comment_content = context[:end]
            del (context[:end + 1])
        elif start < end:
            comment_content = context[start+1:end]
            del (context[start:end + 1])
        context.insert(start, MultilineComment(comment_content))


def strip_off_one_line_comments(context):
    while True:
        try:
            start = context.index(START_ONE_LINE_COMMENT)
        except ValueError:
            return context

        try:
            eof_index = context[start + 1:].index(NEW_LINE)
        except ValueError:
            eof_index = sys.maxsize
        abs_eof_index = start + eof_index + 1
        one_line_comment_contents = context[start+1:abs_eof_index]
        del (context[start:abs_eof_index])
        context.insert(start, OneLineComment(one_line_comment_contents))


def find_not_escaped_double_quote(token_list):
    QUOTE = Quote()
    BACKSLASH = Backslash()
    index_to_start_search = 0
    while True:
        try:
            ind = token_list[index_to_start_search:].index(QUOTE)
            i = ind - 1
            while i >= 0 and token_list[index_to_start_search + i] == BACKSLASH:
                i -= 1
            if (ind - i) % 2 == 1:
                return index_to_start_search + ind
            else:
                index_to_start_search = index_to_start_search + ind + 1
        except ValueError:
            return None


def strip_off_string_literals(token_list):
    list_len = len(token_list)
    logging.debug(f"Memory used to store token list: {sys.getsizeof(token_list)}, length: {list_len}")
    while True:
        opening_quote_index = find_not_escaped_double_quote(token_list)
        logging.debug(f"Processing now element {opening_quote_index} out of {list_len}")
        if opening_quote_index is None:
            return token_list
        closing_quote_index = find_not_escaped_double_quote(token_list[opening_quote_index + 1:])
        if closing_quote_index is None:
            print(f'Warning: closing bracket is not found: {token_list[opening_quote_index + 1:]}')
            closing_quote_index = sys.maxsize
        abs_closing_quote_index = opening_quote_index + 1 + closing_quote_index
        string_literal_content = token_list[opening_quote_index+1: abs_closing_quote_index]
        del (token_list[opening_quote_index: abs_closing_quote_index + 1])
        token_list.insert(opening_quote_index, StringLiteral(string_literal_content))


def strip_off_identifiers(identifiers_to_ignore, context):
    non_identifiers = set(
        key_words + two_character_tokens + one_character_tokens + one_char_verbose + two_char_verbose + \
        list(placeholders.values()) + tabs + identifiers_to_ignore)

    result = []
    for word in context:
        if not is_number(word) and word not in non_identifiers:
            result.append(placeholders['identifier'])
        else:
            result.append(word)
    return result


def process_number_literal(possible_number):
    if is_number(possible_number) and possible_number not in tabs:
        parts_of_number = []
        if possible_number.startswith('-'):
            parts_of_number.append('-')
            possible_number = possible_number[1:]
        if possible_number.startswith("0x"):
            parts_of_number.append(HexStart())
            possible_number = possible_number[2:]
            hex = True
        else:
            hex = False
        for ch in possible_number:
            if ch == '.':
                parts_of_number.append(DecimalPoint())
            elif ch == 'l' or ch == 'L':
                parts_of_number.append(L())
            elif (ch == 'f' or ch == 'F') and not hex:
                parts_of_number.append(F())
            elif (ch == 'd' or ch == 'D') and not hex:
                parts_of_number.append(D())
            elif (ch == 'e' or ch == 'E') and not hex:
                parts_of_number.append(E())
            else:
                parts_of_number.append(ch)
        return Number(parts_of_number)
    else:
        return ProcessableToken(possible_number)


def process_numeric_literals(token_list):
    res = []
    for token in token_list:
        if isinstance(token, ProcessableToken):
            numbers_separated = list(filter(None, re.split(f'(?:^|(?<=[^a-zA-Z0-9]))({NUMBER_REGEX})(?=[^a-zA-Z0-9.]|$)', token.get_val())))
            for possible_number in numbers_separated:
               res.append(process_number_literal(possible_number))
        elif isinstance(token, ProcessableTokenContainer):
            for subtoken in token.get_subtokens():
                res.extend(process_numeric_literals(subtoken))
        else:
            res.append(token)
    return res
