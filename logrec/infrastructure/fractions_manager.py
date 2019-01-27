import logging
import os
from typing import Callable, Generator

import pandas

from logrec.util.files import file_mapper

logger = logging.getLogger(__name__)

N_CHUNKS = 1000


def percent_to_chunk(percent: float) -> int:
    return int(percent * N_CHUNKS * 0.01)


def check_max_precision(fl: float, prec: int) -> bool:
    n = int(fl * 10 ** prec) / float(10 ** prec)
    return n == fl


def check_value_ranges(percent: float, start_from: float) -> None:
    if percent <= 0.0 or percent > 100.0:
        raise ValueError(f"Wrong value for percent: {percent}")
    if start_from < 0.0:
        raise ValueError(f"Start from cannot be negative: {start_from}")
    if percent + start_from > 100.0:
        raise ValueError(f"Wrong values for percent ({percent}) "
                         f"and start_from ({start_from})")


def normalize_string(val: float) -> str:
    if int(val * 10) % 10 == 0:
        return f'{int(val)}'
    else:
        return f'{val:.1f}'


def normalize_percent_data(percent: float, start_from: float) -> (str, str):
    check_max_precision(percent, 1)
    check_max_precision(start_from, 1)
    check_value_ranges(percent, start_from)
    return normalize_string(percent), normalize_string(start_from)


def get_percent_prefix(percent: float, start_from: float):
    normalized_percent, normalized_start_from = normalize_percent_data(percent, start_from)
    return f"{normalized_percent}_{'' if normalized_start_from == '0' else (normalized_start_from + '_')}"


def get_chunk_from_filename(filename: str) -> int:
    try:
        underscore_index = filename.index("_")
    except ValueError as e:
        raise ValueError(f"Filename is not in format <chunk>_<model name>: {filename}") from e
    return int(filename[:underscore_index])


def include_to_df(filename: str, percent: float, start_from: float) -> bool:
    check_value_ranges(percent, start_from)

    basename = os.path.basename(filename)
    if basename.startswith("_"):
        return False
    chunk = get_chunk_from_filename(basename)
    return percent_to_chunk(start_from) <= chunk < percent_to_chunk(start_from + percent)


def include_to_df_tester(percent: float, start_from: float) -> Callable:
    def tmp(filename):
        return 1 if include_to_df(filename, percent, start_from) else 0

    return tmp


def reverse_line(line):
    lst = line.split(" ")
    lst.reverse()
    return " ".join(lst)


def create_df_gen(dir: str, percent: float, start_from: float, backwards: bool) \
        -> Generator[pandas.DataFrame, None, None]:
    lines = []
    files_total = sum(f for f in file_mapper(dir, include_to_df_tester(percent, start_from),
                                             extension=None, ignore_prefix="_"))

    DATAFRAME_LINES_THRESHOLD = 20000
    cur_file = 0
    at_least_one_frame_created = False
    for root, dirs, files in os.walk(dir):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                if include_to_df(file, percent, start_from):
                    cur_file += 1
                    logger.debug(f'Adding {os.path.join(root, file)} to dataframe [{cur_file} out of {files_total}]')
                    for line in f:
                        if backwards:
                            line = reverse_line(line)
                        lines.append(line)
                    if len(lines) > DATAFRAME_LINES_THRESHOLD:
                        logger.debug("Submitting dataFrame...")
                        yield pandas.DataFrame(lines)
                        lines = []
                        at_least_one_frame_created = True
    if lines:
        yield pandas.DataFrame(lines)
        at_least_one_frame_created = True
    if not at_least_one_frame_created:
        raise ValueError(f"No data available: {os.path.abspath(dir)}")
