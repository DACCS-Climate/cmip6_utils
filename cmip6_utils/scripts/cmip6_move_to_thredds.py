#!/home/dchandan/mambaforge/bin/python
import argparse
import os
import sys
from os.path import join
from shutil import move, rmtree

from cmip6_utils.cli import add_common_parser_args, set_default_activitydir
from cmip6_utils.dir import get_cmip_directories_at_level
from cmip6_utils.misc import BC


def cli():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            "This script copies datasets from the staging directory to a directory that is "
            "served by the THREDDS servre."
        ),
        epilog=(
            "Note: This is the FINAL step of the processing pipeline. Only run this script "
            "if you are 100% sure that all pre-processing up to this point has completed correctly."
        ),
    )
    add_common_parser_args(parser, exp=True, adir=True, dryrun=True)
    parser.add_argument(
        "--threddsdir",
        "-D",
        type=str,
        default="/data/birdhouse-persist/ncml",
        help="Location for CMIP6 data. The directory must contain the 'CMIP6' folder.",
    )

    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])
    set_default_activitydir(args)
    return args


def main():
    args = cli()

    exp_str = args.experiment
    varname_str = f"/{args.variable}/"

    count = 0

    _tmp = args.activitydir.strip("/").split("/")
    _i = _tmp.index("CMIP6")
    rootdir = "/" + "/".join(_tmp[:_i])

    for root, dirs, _ in get_cmip_directories_at_level(args.activitydir, 7):  # here 'dirs' are the version directories
        if exp_str in root and varname_str in root:
            if len(dirs) > 1:
                raise RuntimeError(
                    (
                        "More than one version of this dataset found. "
                        "Run 'cmip6_find_duplicate_versions' first to trim to latest version."
                    )
                )
            else:
                version = dirs[0]
                source_dir = join(root, version)
                print(BC.okgreen(f"Source: {source_dir}"))
                dest_dir = root.replace(rootdir, args.threddsdir)
                print(f"Destination : {dest_dir}")
                if not args.dry_run:
                    os.makedirs(dest_dir, exist_ok=True)
                    move(source_dir, dest_dir)

                # Now that files have been moves from the staging directory, I remove the directory sub-there
                # that is empty
                empty_sub_tree = "/" + "/".join(root.strip("/").split("/")[:-1])
                print(f"Removing: {empty_sub_tree}")
                assert empty_sub_tree.endswith(args.variable)
                if not args.dry_run:
                    rmtree(empty_sub_tree)
                # break

            count += 1

    print("\n")
    print(f"Moved {count} datasets")
    if args.dry_run:
        print(BC.warn("******************** DRY RUN COMPLETE ********************"))


if __name__ == "__main__":
    main()
