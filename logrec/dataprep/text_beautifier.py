import re

from logrec.dataprep.preprocessors.model.placeholders import placeholders, placeholders_beautiful, separators_beautiful
from logrec.dataprep.split.ngram import SplitRepr

cc = placeholders['camel_case_separator']
we = placeholders['split_words_end']


def cap_non_init_cc_words(w):
    sub = re.sub(f'{placeholders["camel_case_separator"]} (.*?) (?={placeholders["camel_case_separator"]}|$)',
                 lambda n: "".join(n.group(1).capitalize().split(" ")), w)
    return sub


def sep_boundaries(m):
    return "".join(m.group(1).split(" ")) + (
        cap_non_init_cc_words(m.group(2)) if m.group(2) != "" else ""
    )


def restore_tabs(text: str) -> str:
    for i in range(1, 11):
        text = text.replace('\\t' + str(i), ' ' * 4 * i)
    return text


def restore_words_from_subwords(text: str) -> str:
    if text.find(placeholders['split_words_end']) == -1:
        splitRepr = SplitRepr.BETWEEN_WORDS
    else:
        splitRepr = SplitRepr.BONDERIES
    if splitRepr == SplitRepr.BETWEEN_WORDS:
        text = re.sub(f"{placeholders['camel_case_separator']} (\S+)",
                      lambda m: m.group(1).capitalize(), text)
    else:
        text = re.sub(f"{cc} ((?:\S+ )*?)((?:{cc} (?:\S+ )*?)*){we}",
                      sep_boundaries,
                      text)

    for k, v in separators_beautiful.items():
        text = text.replace(" " + placeholders[k] + " ", v)

    return text


def restore_capitalization(text: str) -> str:
    text = re.sub(placeholders["capital"] + " (\S+)",
                  lambda m: m.group(1).capitalize(), text)
    text = re.sub(f"{cc} {placeholders['capitals']}( .*?)(?={cc}|{we})", lambda m: cc + m.group(1).upper(), text)
    text = re.sub(placeholders["capitals"] + " (\S+)",
                  lambda m: m.group(1).upper(), text)
    return text


def beautify_placeholders(text: str) -> str:
    for k, v in placeholders_beautiful.items():
        text = text.replace(placeholders[k], v)
    return text


def break_lines(text):
    return re.sub(' ?({|}|;|\*/) ?',
                  lambda m: f'{m.group(1)}\n', text)


def collapse_pads(text):
    p = placeholders['pad_token']
    match = re.search(f'({p} )*{p}', text)
    if match:
        num = len(match.group(0).split(" "))
        text = re.sub(f'({p} )*{p}', f'{num}x{p}', text)
    return text


def beautify_text(text: str) -> str:
    text = restore_capitalization(text).replace('<eos>', '\n')
    text = collapse_pads(text)
    text = beautify_placeholders(text)

    text = restore_words_from_subwords(text)
    text = restore_tabs(text)
    text = text.replace(' . ', '.')
    text = break_lines(text)
    return text
