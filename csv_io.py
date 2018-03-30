__author__ = 'hlib'

import csv

def write_to_classification_spreadsheet(logs):
    n_chunks = len(logs) // 50000 + 1
    print("There are " + str(len(logs)) + " logs. Writing them into " + str(n_chunks) + " files")
    log_sets = [logs[i::n_chunks] for i in range(n_chunks)]
    for index, log_set in enumerate(log_sets):
        with open('logs' + str(index) + '.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for log in log_set:
                writer.writerow([log.log_text, log.log_level, log.n_variables,
                                 log.first_word_cathegory, log.context_before + log.log_text_line + log.context_after,
                                 len(log.log_text), log.link])


def output_frequencies(filename, frequencies, sorted_project_list):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        header = ['word', 'median', 'mean', 'found in projects']
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