import argparse
import os
from typing import Optional

from cmip6_utils.cmip6 import cmip6_activities


class CMIPDirLevels:
    institution = 1
    source = 2
    experiment = 3
    variant = 4
    table = 5
    variable = 6
    grid = 7
    version = 8


def walk_cmip_directory(root_dir: str, level: Optional[int] = None) -> list[str]:
    """
    Like a typical os.walk, except the depth of the walk terminates at a specified depth level.
    If level is not specified then it works like os.walk.

    Modified from https://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below
    """

    # if not root_dir.removesuffix("/").endswith("CMIP"):
    #     raise RuntimeError("For walk_cmip_directory to work, the root directory must end in 'CMIP'")

    if root_dir.removesuffix("/").split("/")[-1] not in cmip6_activities:
        raise RuntimeError(
            "For get_cmip_directories_at_level to work, the root directory must end in a CMIP6 " "activity ID."
        )

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

    # if not root_dir.removesuffix("/").endswith("CMIP"):
    #     raise RuntimeError("For get_cmip_directories_at_level to work, the root directory must end in 'CMIP'")

    if root_dir.removesuffix("/").split("/")[-1] not in cmip6_activities:
        raise RuntimeError(
            "For get_cmip_directories_at_level to work, the root directory must end in a CMIP6 " "activity ID."
        )

    sep = os.path.sep
    some_dir = root_dir.rstrip(sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(sep)
    for root, dirs, files in os.walk(some_dir):
        num_sep_this = root.count(sep)
        if num_sep + level <= num_sep_this:
            yield root, dirs, files
            del dirs[:]
