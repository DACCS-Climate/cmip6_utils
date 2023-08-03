import os
import argparse


class CMIPDirLevels:
    institution = 1
    source = 2
    experiment = 3
    variant = 4
    table = 5
    variable = 6
    grid = 7
    version = 9


def walk_cmip_directory(root_dir, level=None):
    """
    Like a typical os.walk, except the depth of the walk terminates at a specified depth level.
    If level is not specified then it works like os.walk.

    Modified from https://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below
    """
    if level is None:
        yield from os.walk(root_dir)
        return

    sep = os.path.sep
    some_dir = root_dir.rstrip(sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]


def get_cmip_directories_at_level(root_dir: str, level: int) -> list[str]:
    """
    Walks through a CMIP data directory structure and returns the directories and files at a specific
    directory level.

    Modified from https://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below
    """
    sep = os.path.sep
    some_dir = root_dir.rstrip(sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(sep)
    for root, dirs, files in os.walk(some_dir):
        num_sep_this = root.count(sep)
        if num_sep + level <= num_sep_this:
            yield root, dirs, files
            del dirs[:]


def main():
    # for root, dirs, files in get_cmip_directories_at_level("CMIP", CMIPDirLevels.source):
    #     print(root)
    for root, dirs, files in walk_cmip_directory("CMIP"):
        print(root)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("variable", type=str, help="Name of the vrabiable to check")
    # args = parser.parse_args()
    main()
