import argparse
import os
import sys
from os.path import join
from shutil import move

from cmip6_utils.dir import get_cmip_directories_at_level
from cmip6_utils.misc import BC


def cli():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(""),
        epilog="Note: This script should be called only after combined timeseries files have been generated.",
    )
    parser.add_argument("variable", type=str, help="Name of the CMIP6 variable")
    parser.add_argument("experiment", type=str, help="Name of the CMIP6 experiment")
    parser.add_argument(
        "--rootdir",
        "-d",
        type=str,
        default="/data/Datasets",
        help="Location for CMIP6 data. The directory must contain the 'CMIP6' folder.",
    )
    parser.add_argument(
        "--dry-run",
        "-t",
        action="store_true",
        help=(
            "Dry run. Does not move/remove any files. "
            "This will simply print the processing it will do and then exit. Useful as a first "
            "step before making changes."
        ),
    )
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])
    return args


def main():
    args = cli()

    exp = args.experiment
    varname = f"/{args.variable}/"

    rootdir = args.rootdir
    cmip_dir = join(rootdir, "CMIP6/CMIP")

    for root, dirs, files in get_cmip_directories_at_level(cmip_dir, 7):
        if exp in root and varname in root:
            if len(dirs) != 1:
                print("\n")
                print(root)
                # sorting the list of versions
                dirs = sorted(dirs)
                # we keep the last version from the sorted list
                dir_to_keep = dirs[-1]
                for _dir in dirs:
                    if _dir == dir_to_keep:
                        print(BC.okgreen(f"   Keeping version {_dir}"))
                    else:
                        print(BC.warn(f"   Removing version {_dir}"))
                        new_root = root.replace(
                            "/CMIP6/", "/CMIP6_duplicate_versions_deleted/"
                        )
                        print(f"   Moving contents to {new_root}")
                        if not args.dry_run:
                            os.makedirs(new_root, exist_ok=True)
                            move(join(root, _dir), join(new_root, _dir))
                            print("   Move successful")


if __name__ == "__main__":
    main()
