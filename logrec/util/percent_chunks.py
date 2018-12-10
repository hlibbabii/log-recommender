def check_max_precision(fl, prec):
    n = int(fl * 10 ** prec) / float(10 ** prec)
    return n == fl


def check_value_ranges(percent, start_from):
    if percent <= 0.0 or percent > 100.0:
        raise ValueError(f"Wrong value for percent: {percent}")
    if start_from < 0.0:
        raise ValueError(f"Start from cannot be negative: {start_from}")
    if percent + start_from > 100.0:
        raise ValueError(f"Wrong values for percent ({percent}) "
                         f"and ({start_from})")


def normalize_string(val):
    if int(val * 10) % 10 == 0:
        return f'{int(val)}'
    else:
        return f'{val:.1f}'


def normalize_percent_data(percent, start_from):
    check_max_precision(percent, 1)
    check_max_precision(start_from, 1)
    check_value_ranges(percent, start_from)
    return normalize_string(percent), normalize_string(start_from)


def get_chunk_prefix(filename):
    underscore_index = filename.index("_")
    if underscore_index == -1:
        raise ValueError(f"Filename is not in format <chunk>_<model name>: {filename}")
    return filename[:underscore_index]
