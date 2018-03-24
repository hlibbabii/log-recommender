import operator
from pprint import pprint
import re
from math import log
from log_picker import test_pick_log
from log_statement import LogStatement
import os

__author__ = 'hlib'

LOG_LEVEL_REGEX = re.compile(".*([Ll]og|LOG)\.([Tt]race|[Dd]ebug|[Ii]nfo|[Ww]arn|[Ee]rror|[Ff]atal)\(.*\).*")

VAR_PLACEHOLDER = "<VAR>"
STRING_RESOURCE_PLACEHOLDER = "<STRING_RESOURCE>"

def extract_log_level(line):
    matcher = re.match(LOG_LEVEL_REGEX, line)
    if matcher is not None:
        return matcher.group(2).lower()
    else:
        print("Log level couldn't be extracted from log statement: " + line)
        return "Unknown"

def extract_text_and_variables(line):
    full_line = line
    text = ""
    text_parts = 0
    opening_quote_index = line.find("\"")
    while opening_quote_index >= 0:
        line = line[opening_quote_index + 1:]
        closing_quote_index = line.find("\"")
        if closing_quote_index < 0:
            print("No closing quote found for the opening quote in string: " + full_line)
            return "", 0
        text += line[:closing_quote_index]
        text_parts += 1
        line = line[closing_quote_index+1:]
        opening_quote_index = line.find("\"")
    if line.find("+") >= 0:
        text_parts += 1
    if text_parts > 1:
        n_variables = text_parts - 1
    else:
        n_variables = text.count("{}")
        if n_variables == 0:
            n_variables = text.count("%")
    return text, n_variables


def contains_text(line):
    return line.find("\"") >= 0

def append_period_if_absent(line):
    if len(line) > 0:
        if line[-1] not in ['.', '!', '?']:
            line += "."
    return line


def replace_string_resources_names(line):
    changed = re.sub('^([0-9a-zA-Z]+\\.)+[0-9a-zA-Z]+$', STRING_RESOURCE_PLACEHOLDER, line)
    if changed != line:
        print(line + "  ----->  " + changed)
    return changed


def replace_variable_place_holders(line):
    changed = re.sub('\\{\\}', VAR_PLACEHOLDER, line)
    changed = re.sub('%[0-9]*[a-z]', VAR_PLACEHOLDER, changed)
    if changed != line:
        print(line + "  ----->  " + changed)
    return changed


def postprocess_extracted_text(line):
    line = line.strip()
    line = replace_string_resources_names(line)
    line = replace_variable_place_holders(line)
    # line = append_period_if_absent(line)
    return line


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]


def split_to_key_words_and_identifiers(line):
    return list(filter(None, re.split("[\[\] ,.\-!?:\n\t(){};=+*/\"&|<>_#\\\@$]+", line)))


def preprocess_context(context):
    context = split_to_key_words_and_identifiers(context)
    context = [item.lower() for identifier in context for item in camel_case_split(identifier)]
    return context

STOP_REGEX = re.compile(".*is(Trace|Debug|Info|Warn)Enabled.*")

def filter_bad_context_line(new_context_line):
    return re.match(STOP_REGEX, new_context_line) is None


def read_grepped_log_file(directory):
    list= []
    for filename in os.listdir(directory):
        with open(os.path.join(directory, filename), 'r') as f:
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
        map(lambda l: process_log_statement(l), logs)
    )


def remove_placeholders(log_text):
    log_text = re.sub(VAR_PLACEHOLDER, r'', log_text)
    log_text = re.sub(STRING_RESOURCE_PLACEHOLDER, r'', log_text)
    return log_text

def get_words_from_log_text(log_text):
    #Consider different splitting for log statement than for the context
    log_text = remove_placeholders(log_text)
    log_text = log_text.lower()
    return split_to_key_words_and_identifiers(log_text)


def filter_out_stop_words(words_from_log_text):
    return list(filter(lambda w: w not in STOP_WORDS, words_from_log_text))


FIRST_WORDS = ["received", "failed", "sending", "starting", "got", "created", "caught", "stopping",
               "creating", "waiting", "exception", "message", "error", "attempting", "removing", "finished",
               "testing", "adding", "started", "ignoring", "unexpected", "using", "no", "found", "start",
               "processing", "adding", "expected", "cannot", "running", "setting", "closing", "unable", "deleting",
               "skipping", "executing", "added", "connecting", "testing", "shutting", "initializing", "successfully",
               "restarting", "updating"]


def process_log_statement(log_entry):
    text, n_variables = extract_text_and_variables(log_entry['log_statement'])
    log_text = postprocess_extracted_text(text)
    words_from_log_text = get_words_from_log_text(log_text)
    first_word = ""
    if len(words_from_log_text) > 0:
        first_word=words_from_log_text[0]
    first_word_cathegory = "OTHER__"
    if first_word in FIRST_WORDS:
        first_word_cathegory = first_word
    words_from_log_text = filter_out_stop_words(words_from_log_text)
    return LogStatement(
            log_text=log_text,
            log_first_word=first_word,
            first_word_cathegory=first_word_cathegory,
            log_text_words=words_from_log_text,
            log_level=extract_log_level(log_entry['log_statement']),
            n_variables=n_variables,
            context=log_entry['context'],
            context_words=preprocess_context(log_entry['context']),
            link=log_entry['github_link'])


def get_idfs(context_list):
    sum = dict()
    vector_number = float(len(context_list))
    for l in context_list:
        for context_string in l:
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
            f.write(l.log_level + " " + str(l.n_variables) + "\n")
            f.write(str(l.context) + "\n")
            f.write(l.link + "\n")
            f.write("\n")
        f.write(str(idfs))


def output_to_file(preprocessed_logs, sorted_idf_tuples):
    output(preprocessed_logs, sorted_idf_tuples, '../gengram/corpus.txt')

STOP_WORDS=["a", "an", "and", "are", "as", "at", "be", "for", "has", "in", "is", "it", "its", "of", "on", "that",
            "the", "to", "was", "were", "with"]
#the following words are normally stop words but we might want not to consider as stop words:  by, from, he, will

def get_frequencies_for_log_texts(logs):
    dict = {}
    for l in logs:
        for w in l.log_text_words:
            if w in dict:
                dict[w] += 1
            else:
                dict[w] = 1
    return dict


def get_first_word_frequencies(logs):
    dict = {}
    for l in logs:
        w = l.log_first_word
        if w in dict:
            dict[w] += 1
        else:
            dict[w] = 1
    return dict


if __name__ == "__main__":
    in_file = "../.Logs"
    grepped_logs = read_grepped_log_file(in_file)
    preprocessed_logs = preprocess_grepped_logs(grepped_logs)
    frequencies = get_frequencies_for_log_texts(preprocessed_logs)
    first_word_frequencies = get_first_word_frequencies(preprocessed_logs)
    pprint(sorted(first_word_frequencies.items(), key=operator.itemgetter(1), reverse=True))
    sorted_idf_tuples, idfs = get_idfs(list(map(lambda l: l.context_words, preprocessed_logs)))

    output_to_file(preprocessed_logs, sorted_idf_tuples)
    test_pick_log(preprocessed_logs, idfs)
    from csv_io import write
    write(preprocessed_logs)

