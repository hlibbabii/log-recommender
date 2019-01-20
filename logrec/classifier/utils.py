import os


def get_dir_and_file(path_to_file):
    dir, file = os.path.split(path_to_file)
    return os.path.join(os.path.basename(dir), file)


def get_two_levels_subdirs(dir):
    subdirs = next(os.walk(dir))[1]
    for subdir in subdirs:
        for subsubdir in next(os.walk(os.path.join(dir, subdir)))[1]:
            yield dir, subdir, subsubdir
