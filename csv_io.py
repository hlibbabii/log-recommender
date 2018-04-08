import os
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload
import httplib2
from google_drive_api_utils import get_credentials

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


def output_frequencies(filename, frequencies, sorted_project_list):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        header = ['word', 'median', 'mean', 'found times', 'found in projects']
        header.extend(sorted_project_list)
        writer.writerow(header)
        for word in frequencies:
            proj_freqs = map(lambda x: word[1][x] if x in word[1] else 0.0, sorted_project_list)
            line = [word[0],
                             word[1]['__median__'],
                             word[1]['__all__'],
                             word[1]['__all_abs__'],
                             word[1]['__found_in_projects__']]
            line.extend(proj_freqs)
            writer.writerow(line)


def output_log_level_freqs_by_first_word(filename, frequencies, levels):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        header = ['word', 'weighted avg', 'all']
        header.extend(levels)
        writer.writerow(header)
        for word in frequencies:
            proj_freqs = map(lambda x: word[1][x] if x in word[1] else 0.0, levels)
            line = [word[0], word[1]['__weighted_avg__'], word[1]['__all__']]
            line.extend(proj_freqs)
            writer.writerow(line)


def output_variable_freqs_by_first_word(filename, frequencies, keys):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        header = ['word', 'all']
        header.extend(keys)
        header.extend(['more vars'])
        writer.writerow(header)
        for word in frequencies:
            proj_freqs = map(lambda x: word[1][x] if x in word[1] else 0.0, keys)
            line = [word[0], word[1]['__all__']]
            line.extend(proj_freqs)
            line.extend([word[1]['__more_vars__']])
            writer.writerow(line)


def upload_to_google(dir):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)
    files = drive_service.files()
    file_counter = 0
    for filename in os.listdir(dir):
        file_counter += 1
        print("Uploading file " + str(file_counter) + " to Google drive...")
        file_metadata = {
            'name': filename,
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }
        media = MediaFileUpload(os.path.join(dir, filename),
                                mimetype='text/csv',
                                resumable=True)
        files.create(body=file_metadata, media_body=media).execute()