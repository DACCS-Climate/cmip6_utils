import os
import os.path as osp
from argparse import ArgumentParser
from pathlib import Path


def cli():
    parser = ArgumentParser()
    parser.add_argument("variable", type=str, help="Name of the varbiable to check")
    parser.add_argument("experiment", type=str, help="Name of the experiment")
    parser.add_argument(
        "cmip6_data_dir", type=str, help="Directory where the 'CMIP6' root data directory for CMIP6 data is located"
    )
    args = parser.parse_args()
    if not osp.exists(osp.join(args.cmip6_data_dir, "CMIP6")):
        raise ValueError("No 'CMIP6' directory in the supplied location for CMIP6 directory.")

    return args


def main():
    args = cli()

    print(f"Searching for '{args.variable}' files for experiment '{args.experiment}'")

    P = Path(args.cmip6_data_dir)
    dir_count = 0
    files_count = 0
    for dir in P.glob(f"CMIP6/**/{args.experiment}/**/{args.variable}/*/*"):
        dir_count += 1
        # Assumption: there are no non-variable related files in these directories
        files_count += len(os.listdir(dir))

    print(f"Datasets searched: {dir_count}")
    print(f"Files found: {files_count}")


if __name__ == "__main__":
    main()
