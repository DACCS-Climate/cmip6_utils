import argparse
import os
import sys
from os.path import join
from shutil import move

from cmip6_utils.cli import add_common_parser_args, set_default_activitydir
from cmip6_utils.dir import get_cmip_directories_at_level
from cmip6_utils.misc import BC


def cli():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(""),
        epilog="Note: This script should be called only after combined timeseries files have been generated.",
    )
    add_common_parser_args(parser, exp=True, adir=True, dryrun=True)
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])
    set_default_activitydir(args)
    return args


def main():
    args = cli()

    exp = args.experiment
    varname = f"/{args.variable}/"
    for root, dirs, _ in get_cmip_directories_at_level(args.activitydir, 7):
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
                        new_root = root.replace("/CMIP6/", "/CMIP6_duplicate_versions_deleted/")
                        print(f"   Moving contents to {new_root}")
                        if not args.dry_run:
                            os.makedirs(new_root, exist_ok=True)
                            move(join(root, _dir), join(new_root, _dir))
                            print("   Move successful")

    if args.dry_run:
        print(BC.warn("******************** DRY RUN COMPLETE ********************"))


if __name__ == "__main__":
    main()
