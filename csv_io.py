__author__ = 'hlib'

import csv

def write(logs):
    with open('logs.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for log in logs:
            writer.writerow([log.log_text, log.log_level, log.n_variables,
                             log.first_word_cathegory, log.context + log.log_text_line, len(log.log_text), log.link])
