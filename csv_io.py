__author__ = 'hlib'

import csv

def write_to_classification_spreadsheet(dir_name, logs):
    n_chunks = len(logs) // 50000 + 1
    print("There are " + str(len(logs)) + " logs. Writing them into " + str(n_chunks) + " files")
    log_sets = [logs[i::n_chunks] for i in range(n_chunks)]
    for index, log_set in enumerate(log_sets):
        with open(dir_name + '/logs' + str(index) + '.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for log in log_set:
                writer.writerow([log.log_text, log.log_level, log.n_variables,
                                 log.first_word_cathegory, log.context_before + log.log_text_line + log.context_after,
                                 len(log.log_text), log.link])

def output_to_csv(filename, header, lambda1, dim1, dim2):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        for row in dim1:
            writer.writerow(lambda1(row, dim2))