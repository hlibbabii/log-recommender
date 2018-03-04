import re

__author__ = 'hlib'


def extract_text(line):
    full_line = line
    text = ""
    opening_quote_index = line.find("\"")
    while opening_quote_index >= 0:
        line = line[opening_quote_index + 1:]
        closing_quote_index = line.find("\"")
        if closing_quote_index < 0:
            raise ValueError("No closing quote found for the opening quote in string: " + full_line)
        text += line[:closing_quote_index]
        line = line[closing_quote_index+1:]
        opening_quote_index = line.find("\"")
    return text


def contains_text(line):
    return line.find("\"") >= 0

def appendPeriodIfAbsent(line):
    if len(line) > 0:
        if line[-1] not in ['.', '!', '?']:
            line += "."
    return line


def replaceStringResourcesNames(line):
    return re.sub('^([0-9a-zA-Z]+\\.)+[0-9a-zA-Z]+$', '<STRING_RESOURCE>', line)

def postprocess_extracted_text(line):
    line = line.strip()
    changed = replaceStringResourcesNames(line)
    if changed != line:
        print(line + "  ----->  " + changed)
    line = changed
    line = appendPeriodIfAbsent(line)
    return line


def preprocess(filename):
    with open(filename, 'r') as f:
        for line in f:
            if contains_text(line):
                try:
                    yield postprocess_extracted_text(extract_text(line))
                except ValueError as err:
                    print(err)


def output(input_filename, output_filename):
    with open(output_filename, 'w') as f:
        for preprocessed_line in preprocess(input_filename):
            f.write(preprocessed_line + "\n")


if __name__ == "__main__":
    in_file = "../grepped_logs.20180301-002126"
    output(in_file, '../gengram/corpus.txt')
