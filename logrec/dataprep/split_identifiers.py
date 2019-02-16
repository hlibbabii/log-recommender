import os

from logrec import base_project_dir
from logrec.cli import preprocess
from logrec.dataprep.prepconfig import PrepParam, PrepConfig

prep_configs = [
    '002000',
    '304000',
    '305000',
    '306000',
    '307000',
]

path_to_file = os.path.join(base_project_dir, 'identifiers')
path_to_file_out = os.path.join(base_project_dir, 'identifiers2.csv')

DELIMITER = ','


def gen():
    with open(path_to_file, 'r') as f:
        identifiers = [line.rstrip('\n') for line in f]

    csv_lines = [DELIMITER.join(["config"] + [p for p in PrepParam] + identifiers)]
    for prep in prep_configs:
        csv_line = [prep]
        for p in PrepParam:
            csv_line.append(
                PrepConfig.human_readable_values[p][PrepConfig.from_encoded_string(prep).get_param_value(p)])
        for identifier in identifiers:
            tokens = preprocess(identifier, prep)
            csv_line.append(' '.join(tokens))
        csv_lines.append(DELIMITER.join(csv_line))

    with open(path_to_file_out, 'w') as f:
        for line in csv_lines:
            f.write(f'{line}\n')


if __name__ == '__main__':
    gen()
