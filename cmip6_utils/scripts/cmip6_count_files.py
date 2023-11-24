#!/usr/bin/env python
"""
This is a check/verification utility. It counts the number of dataset directories
for the user-provided variable-experiment combination, as well as the number of files
in each of them.

When the variable has been post-processed to merge all the individual files into one
then the number of datasets and files should be the same.

E.g. Datasets searched: 823
     Files found: 823

"""

import argparse
import os
import sys
from pathlib import Path

from cmip6_utils.cli import add_common_parser_args, set_default_rootdir


def cli():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            "This is a check/verification utility. It counts the number of dataset directories "
            "for the user-provided variable-experiment combination, as well as the number of files "
            "in each of them. "
            "When the variable has been post-processed to merge all the individual files into one "
            "then the number of datasets and files should be the same (assuming no empty dataset direcs.)."
        ),
    )
    add_common_parser_args(parser, exp=True)
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])
    set_default_rootdir(args)
    return args


def main():
    args = cli()

    print(f"Searching for '{args.variable}' files for experiment '{args.experiment}'")

    P = Path(args.rootdir)
    dir_count = 0
    files_count = 0
    # for dir in P.glob(f"CMIP6/**/{args.experiment}/**/{args.variable}/*/*"):
    for dir in P.glob(f"**/{args.experiment}/**/{args.variable}/*/*"):
        dir_count += 1
        # Assumption: there are no non-variable related files in these directories
        files_count += len(os.listdir(dir))
        if len(os.listdir(dir)) == 0:
            print(dir)

    print(f"Datasets searched: {dir_count}")
    print(f"Files found: {files_count}")


if __name__ == "__main__":
    main()
