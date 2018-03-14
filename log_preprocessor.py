import operator
import re
from math import log
from log_picker import test_pick_log
from log_statement import LogStatement

__author__ = 'hlib'


def extract_text(line):
    full_line = line
    text = ""
    opening_quote_index = line.find("\"")
    while opening_quote_index >= 0:
        line = line[opening_quote_index + 1:]
        closing_quote_index = line.find("\"")
        if closing_quote_index < 0:
            print("No closing quote found for the opening quote in string: " + full_line)
            return None
        text += line[:closing_quote_index]
        line = line[closing_quote_index+1:]
        opening_quote_index = line.find("\"")
    return text


def contains_text(line):
    return line.find("\"") >= 0

def append_period_if_absent(line):
    if len(line) > 0:
        if line[-1] not in ['.', '!', '?']:
            line += "."
    return line


def replace_string_resources_names(line):
    changed = re.sub('^([0-9a-zA-Z]+\\.)+[0-9a-zA-Z]+$', '<STRING_RESOURCE>', line)
    if changed != line:
        print(line + "  ----->  " + changed)
    return changed


def replace_variable_place_holders(line):
    changed = re.sub('\\{\\}', '<VAR>', line)
    changed = re.sub('%[0-9]*[a-z]', '<VAR>', changed)
    if changed != line:
        print(line + "  ----->  " + changed)
    return changed


def postprocess_extracted_text(line):
    if line is None:
        return None
    line = line.strip()
    line = replace_string_resources_names(line)
    line = replace_variable_place_holders(line)
    line = append_period_if_absent(line)
    return line


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]


def split_to_key_words_and_identifiers(line):
    return list(filter(None, re.split("[\[\] ,.\-!?:\n\t(){};=+*/\"&|<>_]+", line)))


def preprocess_context(context):
    context = split_to_key_words_and_identifiers(context)
    context = [item.lower() for identifier in context for item in camel_case_split(identifier)]
    return context

STOP_REGEX = re.compile(".*is(Trace|Debug|Info|Warn)Enabled.*")

def filter_bad_context_line(new_context_line):
    return re.match(STOP_REGEX, new_context_line) is None


def read_grepped_log_file(filename):
    list= []
    with open(filename, 'r') as f:
        n_lines_of_context = int(f.readline())
        while True:
            #reading github link
            github_link = f.readline()
            if not github_link:
                break
            context = ""
            for i in range(n_lines_of_context):
                new_context_line = f.readline()
                if filter_bad_context_line(new_context_line):
                    context += new_context_line
                        #reading log statement
            log_statement_line = f.readline()
            #reading 2 empty lines
            f.readline()
            f.readline()
            if contains_text(log_statement_line):
                list.append({'log_statement': log_statement_line, 'context': context, 'github_link': github_link})
    return list


def preprocess_grepped_logs(logs):
    return list(
        map(lambda l: LogStatement(
            log_text=postprocess_extracted_text(extract_text(l['log_statement'])),
            context=preprocess_context(l['context']),
            link=l['github_link']), logs)
    )


def get_idfs(preprocessed_logs):
    sum = dict()
    vector_number = float(len(preprocessed_logs))
    for l in preprocessed_logs:
        for context_string in l.context:
            if context_string in sum:
                sum[context_string] += 1
            else:
                sum[context_string] = 1
    idfs = {key: log(vector_number / value, 2) for key, value in sum.items()}
    return sorted(idfs.items(), key=operator.itemgetter(1), reverse=True), idfs



def output(preprocessed_logs, idfs, output_filename):
    with open(output_filename, 'w') as f:
        for l in preprocessed_logs:
            f.write(str(l.log_text) + "\n")
            f.write(str(l.context) + "\n\n")
        f.write(str(idfs))


def output_to_file(preprocessed_logs, sorted_idf_tuples):
    output(preprocessed_logs, sorted_idf_tuples, '../gengram/corpus.txt')


if __name__ == "__main__":
    in_file = "grepped_logs.20180313-005759"
    grepped_logs = read_grepped_log_file(in_file)
    preprocessed_logs = preprocess_grepped_logs(grepped_logs)
    sorted_idf_tuples, idfs = get_idfs(preprocessed_logs)

    output_to_file(preprocessed_logs, sorted_idf_tuples)
    test_pick_log(preprocessed_logs, idfs)

