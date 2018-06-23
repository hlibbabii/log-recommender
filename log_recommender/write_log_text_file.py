import argparse

from util import io_utils


def write_log_text_to_corpus_file(preprocessed_logs, output_filename):
    with open(output_filename, 'w') as f:
        for l in preprocessed_logs:
            f.write(str(l.text) + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-corpus-file', action='store', default='')
    args = parser.parse_args()

    preprocessed_logs = io_utils.load_preprocessed_logs()
    write_log_text_to_corpus_file(preprocessed_logs, args.output_corpus_file)