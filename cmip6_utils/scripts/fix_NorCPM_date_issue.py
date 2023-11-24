import argparse
import os
import sys


def cli():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            "The purpose of this script is to download files that were not downloaded by esgpull during "
            "the initial download phase."
        ),
        epilog="Note: This script can only be run after the esgpull download phase has completed.",
    )
    parser.add_argument(
        "variable",
        type=str,
        help="Name of the CMIP6 variable for which to download files",
    )
    parser.add_argument(
        "--rootdir",
        "-d",
        type=str,
        default="/data/Datasets/CMIP6/CMIP",
        help="Root directory for the CMIP6 activity.",
    )

    return parser.parse_args(args=None if sys.argv[1:] else ["--help"])


def main():
    args = cli()
    dir = os.path.join(args.rootdir, "NCC/NorCPM1/historical")
    var = args.variable

    for root, dirs, files in os.walk(dir):
        if files:
            if f"/{var}/" in root:
                # print(files)
                for filename in files:
                    datestart = filename.strip().split("_")[-1]
                    if datestart.startswith("2015") or datestart.startswith("2019"):
                        print(filename)
                        os.remove(os.path.join(root, filename))


if __name__ == "__main__":
    main()
