#!/usr/bin/env python
"""
This is a check/validation utility. It checks that each bottom level directory
in the CMIP6 folder (i.e. each "dataset") only contains a single file (ideally
after the merging process)
"""
import argparse
import os
import sys

from cmip6_utils.cli import add_common_parser_args, set_default_rootdir
from cmip6_utils.dir import CMIPDirLevels, get_cmip_directories_at_level


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Check the CMIP data directory that all bottom level directories "
            "for the supplied variable only contain single files"
        )
    )
    add_common_parser_args(parser, exp=True)
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])
    set_default_rootdir(args)

    experiment = args.experiment

    num_datasets = 0
    for exp_root, dirs, _ in get_cmip_directories_at_level(args.rootdir, CMIPDirLevels.source):
        if experiment in dirs:
            for root, dirs, files in os.walk(os.path.join(exp_root, experiment)):
                if files:  # we have reached the bottom level
                    nfiles = len(files)
                    if f"/{args.variable}/" in root:
                        num_datasets += 1
                        assert nfiles == 1

    print(f"Total datasets checked  : {num_datasets}")


if __name__ == "__main__":
    main()
