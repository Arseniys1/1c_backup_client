import os


def normalize_path(path):
    path = os.path.normcase(path)
    path = os.path.normpath(path)
    path = os.path.realpath(path)
    return path


def remove_slashes(_dir):
    _dir = _dir.replace("/", "")
    _dir = _dir.replace("\"", "")
    return _dir


def remove_space(_dir):
    _dir = _dir.replace(" ", "")
    return _dir


def normalize_dir(_dir):
    _dir = remove_slashes(_dir)
    _dir = remove_space(_dir)
    return _dir

