__author__ = 'hlib'

import csv

def write(logs):
    with open('logs.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for log in logs:
            writer.writerow([log.log_text, log.log_level, log.n_variables,
                             log.first_word_cathegory, log.context + log.log_text_line, len(log.log_text), log.link])


def output_frequencies(frequencies, sorted_project_list):
    with open('frequencies.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        header = ['word', 'median', 'avg', 'found in projects']
        header.extend(sorted_project_list)
        writer.writerow(header)
        for word in frequencies:
            proj_freqs = map(lambda x: word[1][x] if x in word[1] else 0.0, sorted_project_list)
            line = [word[0],
                             word[1]['__median__'],
                             word[1]['__all__'],
                             word[1]['__found_in_projects__']]
            line.extend(proj_freqs)
            writer.writerow(line)