import csv
import logging
import os

from logrec.util import io


def write_to_classification_spreadsheet(dir_name, logs):
    n_chunks = len(logs) // 50000 + 1
    logging.info("There are " + str(len(logs)) + " logs. Writing them into " + str(n_chunks) + " files")
    log_sets = [logs[i::n_chunks] for i in range(n_chunks)]
    for index, log_set in enumerate(log_sets):
        with open(os.path.join(dir_name, f'logs{index}.csv'), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for log in log_set:
                writer.writerow([log.id, log.text, log.level, log.n_variables,
                                 log.first_word_cathegory,
                                 "".join(log.context.context_before) + log.text_line
                                 + "".join(log.context.context_after),
                                 len(log.text), log.link])

if __name__ == '__main__':
    classified_logs = io.load_classified_logs()
    write_to_classification_spreadsheet('../logs', classified_logs)