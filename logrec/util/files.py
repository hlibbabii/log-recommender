import os
from typing import Callable


def get_dir_and_file(path_to_file):
    dir, file = os.path.split(path_to_file)
    return os.path.join(os.path.basename(dir), file)


def get_two_levels_subdirs(dir):
    subdirs = next(os.walk(dir))[1]
    for subdir in subdirs:
        for subsubdir in next(os.walk(os.path.join(dir, subdir)))[1]:
            yield dir, subdir, subsubdir


def file_mapper(dir: str, func: Callable, predicate: Callable[[str], bool] = lambda: True):
    import os
    if not os.path.exists(dir):
        raise ValueError(f"Directory doesnt exist: {dir}")
    for root, dirs, files in os.walk(dir):
        for file in files:
            if predicate(file):
                ret = func(os.path.join(root, file))
                if ret is not None:
                    yield ret
