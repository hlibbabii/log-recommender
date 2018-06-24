import argparse
import logging
import re
import os

from fastai.imports import tqdm
from java_parser import JavaParser
from preprocessors import apply_preprocessors, strip_line, to_lower, split_log_text_to_keywords_and_identifiers, \
    replace_string_resources_names, replace_variable_place_holders, add_ect, spl_verbose
from util import io_utils

from log_statement import LogStatement


__author__ = 'hlib'

LOG_LEVEL_REGEX = re.compile(".*([Ll]og|LOG|[Ll]ogger|LOGGER)\.([Tt]race|[Dd]ebug|[Ii]nfo|[Ww]arn|[Ee]rror|[Ff]atal)\(.*")

def extract_log_level(line):
    matcher = re.match(LOG_LEVEL_REGEX, line)
    if matcher is not None:
        return matcher.group(2).lower()
    else:
        print("Log level couldn't be extracted from log statement: " + line)
        return "Unknown"

def extract_text_and_variables(line):
    java_parser = JavaParser()
    full_line = line
    text = ""
    text_parts = 0
    opening_quote_index = java_parser.find_not_escaped_double_quote(line)
    while opening_quote_index is not None:
        line = line[opening_quote_index + 1:]
        closing_quote_index = java_parser.find_not_escaped_double_quote(line)
        if closing_quote_index is None:
            print("No closing quote found for the opening quote in string: " + full_line)
            return full_line, "", 0
        text += line[:closing_quote_index]
        text_parts += 1
        line = line[closing_quote_index+1:]
        opening_quote_index = java_parser.find_not_escaped_double_quote(line)
    if line.find("+") >= 0:
        text_parts += 1
    if text_parts > 1:
        n_variables = text_parts - 1
    else:
        n_variables = text.count("{}")
        if n_variables == 0:
            n_variables = text.count("%")
    return full_line, text, n_variables


def contains_text(line):
    return line.find("\"") >= 0


def filter_bad_context_line(new_context_line):
    STOP_REGEX = re.compile(".*is(Trace|Debug|Info|Warn)Enabled.*")
    return re.match(STOP_REGEX, new_context_line) is None


def read_grepped_log_file(directory, min_log_number_per_project):
    list= []
    project_stats = {}
    print("returning logs from projects with more than " + str(min_log_number_per_project) + " logs extracted")
    for filename in os.listdir(directory):
        log_counter = 0
        current_proj_list = []
        try:
            with open(os.path.join(directory, filename), 'r') as f:
                n_lines_of_context = int(f.readline())
                while True:
                    #reading github link
                    github_link = f.readline()
                    if not github_link:
                        break

                    context_before = []
                    for i in range(n_lines_of_context):
                        new_context_line = f.readline()
                        if filter_bad_context_line(new_context_line):
                            context_before.append(new_context_line)
                    #reading log statement
                    log_statement_line = f.readline()
                    context_after = []
                    for i in range(n_lines_of_context):
                        new_context_line = f.readline()
                        if filter_bad_context_line(new_context_line):
                            context_after.append(new_context_line)

                    #reading 2 empty lines
                    f.readline()
                    f.readline()
                    if contains_text(log_statement_line):
                        current_proj_list.append({'log_statement': log_statement_line,
                                                  'context_before': context_before,
                                                  'context_after': context_after,
                                     'github_link': github_link, 'project': filename[:filename.index('.')]})
                        log_counter += 1
        except UnicodeDecodeError as er:
            print(er)
            print('Error in file: ' + filename + ". Skipping it.")
            print('The problem occured with log number ' + str(log_counter))

        project_stats[filename] = log_counter
        if log_counter >= min_log_number_per_project:
            list.extend(current_proj_list)
    return list, project_stats


def process_log_statement(log_entry):
    log_text_line, log_text, n_variables = extract_text_and_variables(log_entry['log_statement'])
    words_from_log_text = apply_preprocessors(log_text, [
        strip_line,
        replace_string_resources_names,
        replace_variable_place_holders,
        to_lower,
        spl_verbose,
        add_ect,
        # filter_out_stop_words
    ])
    return LogStatement(
            text_line=log_text_line,
            text_words=words_from_log_text,
            level=extract_log_level(log_entry['log_statement']),
            n_variables=n_variables,
            context_before=log_entry['context_before'],
            context_after=log_entry['context_after'],
            project = log_entry['project'],
            link=log_entry['github_link'])


def preprocess_logs(grepped_logs):
    logging.info(f"Processing logs")
    for ind, grepped_log in tqdm(enumerate(grepped_logs), leave=False, total=logs_total):
        ppl = process_log_statement(grepped_log)
        if len(ppl.text_words) > 0 and len(ppl.context.context_before) > 0:
            yield ppl


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-log-number-per-project', action='store', type=int, default=100)
    args = parser.parse_args()

    in_file = "../../.Logs"
    grepped_logs, project_stats = read_grepped_log_file(in_file, args.min_log_number_per_project)
    pp_logs_gen = []
    logs_total = len(grepped_logs)
    pp_logs_gen = preprocess_logs(grepped_logs)

    io_utils.dump_preprocessed_logs(pp_logs_gen)
    io_utils.dump_project_stats(project_stats)

