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
    changed = re.sub('^([0-9a-zA-Z]+\\.)+[0-9a-zA-Z]+$', '<STRING_RESOURCE>', line)
    if changed != line:
        print(line + "  ----->  " + changed)
    return changed


def replaceVariablePlaceHolders(line):
    changed = re.sub('\\{\\}', '<VAR>', line)
    changed = re.sub('%[0-9]*[a-z]', '<VAR>', changed)
    if changed != line:
        print(line + "  ----->  " + changed)
    return changed


def postprocess_extracted_text(line):
    line = line.strip()
    line = replaceStringResourcesNames(line)
    line = replaceVariablePlaceHolders(line)
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


def output(preprocessed_logs, output_filename):
    with open(output_filename, 'w') as f:
        for preprocessed_line in preprocessed_logs:
            f.write(preprocessed_line + "\n")


if __name__ == "__main__":
    in_file = "grepped_logs.20180305-075743"
    preprocessed_logs = preprocess(in_file)
    output(preprocessed_logs, '../gengram/corpus.txt')
