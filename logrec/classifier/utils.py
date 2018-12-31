import os


def get_dir_and_file(path_to_file):
    dir, file = os.path.split(path_to_file)
    return os.path.join(os.path.basename(dir), file)
