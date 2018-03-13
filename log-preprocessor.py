import operator
import re
from math import log
from sortedcontainers import SortedList

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


def preprocess(filename):
    list= []
    with open(filename, 'r') as f:
        n_lines_of_context = int(f.readline())
        while True:
            #reading github link
            line = f.readline()
            if not line:
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
                try:
                    list.append((postprocess_extracted_text(extract_text(log_statement_line)), preprocess_context(context)))
                except ValueError as err:
                    print(err)
    return list


def get_idfs(preprocessed_logs):
    sum = dict()
    vector_number = float(len(preprocessed_logs))
    for preprocessed_log, context_vector in preprocessed_logs:
        for context_string in context_vector:
            if context_string in sum:
                sum[context_string] += 1
            else:
                sum[context_string] = 1
    idfs = {key: log(vector_number / value, 2) for key, value in sum.items()}
    return sorted(idfs.items(), key=operator.itemgetter(1), reverse=True), idfs



def output(preprocessed_logs, idfs, output_filename):
    with open(output_filename, 'w') as f:
        for preprocessed_line, context in preprocessed_logs:
            f.write(preprocessed_line + "\n")
            f.write(str(context) + "\n\n")
        f.write(str(idfs))


def without_duplicates(list):
    seen = set()
    seen_add = seen.add
    return [x for x in list if not (x in seen or seen_add(x))]


def get_score(context, current_context, idfs):
    current_score = 0.0
    for word1 in without_duplicates(context):
        for word2 in without_duplicates(current_context):
            if word1 == word2:
                current_score += idfs.get(word1)
    return current_score


def get_most_suitable_log_statements(corpus, idfs, current_context, how_many):
    print("Looking for the most suitable log statement for context: " + str(current_context))
    scores = SortedList(key=operator.itemgetter(1))
    for log_statement, context in corpus:
        score = get_score(context, current_context, idfs)
        scores.add(((log_statement, context), score))
    return reversed(scores[-how_many:])


def output_to_file(preprocessed_logs, sorted_idf_tuples):
    output(preprocessed_logs, sorted_idf_tuples, '../gengram/corpus.txt')


def test(preprocessed_logs, idfs):
    print("\n===============Testing=====================\n")
    log_statement_plus_context_to_test = preprocessed_logs[5700]
    most_suitable_log_statements = get_most_suitable_log_statements(preprocessed_logs, idfs, log_statement_plus_context_to_test[1], 10)
    for log_statement_with_context in most_suitable_log_statements:
        print(str(log_statement_with_context[0][0]))
        print(str(log_statement_with_context[0][1]))
        print(str(log_statement_with_context[1]) + "\n")

    print("Real log statement: " + str(log_statement_plus_context_to_test[0]))
    print("Current context: " + str(log_statement_plus_context_to_test[1]))

if __name__ == "__main__":
    in_file = "grepped_logs.20180313-005759"
    preprocessed_logs = preprocess(in_file)
    sorted_idf_tuples, idfs = get_idfs(preprocessed_logs)

    output_to_file(preprocessed_logs, sorted_idf_tuples)
    test(preprocessed_logs, idfs)

