import argparse

from util import io_utils


def write_log_text_to_corpus_files(preprocessed_logs, output_dir):
    with open(f'{output_dir}/train/context.0.src', 'w') as f, open(f'{output_dir}/test/context.0.src', 'w') as g:
        for ind, l in enumerate(preprocessed_logs):
            line = str(l.text) + "\n"
            if ind % 20 >= 3:
                f.write(line)
            else:
                g.write(line)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--log-text-corpus-dir', action='store', default='')
    args = parser.parse_args()

    preprocessed_logs = io_utils.load_preprocessed_logs()
    write_log_text_to_corpus_files(preprocessed_logs, args.output_corpus_file)