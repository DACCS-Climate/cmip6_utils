import os
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace

from cmip6_utils.scripts.cmip6_download_file import cmip6_download_file


def cli() -> Namespace:
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description=(
            "This script can be used to download all available files in a dataset in which "
            "all files are 1 year long. "
            "For example for /the/full/local/path/to/dataset, the script will query all "
            "all available files and download the missing files to that location."
        ),
    )
    parser.add_argument("dataset", type=str, help="Full local path to the dataset to download")
    parser.add_argument(
        "-t",
        type=int,
        help=("Timeout (in seconds) for downloading a file (parameter to requests.get())."),
        default=5,
    )
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])

    if args.dataset.endswith(".nc"):
        raise ValueError("The supplied argument should be the path to the datset, not a specific file")
    return args


def gen_filename_structure(path: str) -> str:
    """Parses the path of the dataset to compose the base filename structure of files in the dataset.
    All filenames start with the structure: variableid_tableid_sourceid_experimentid_variantid_grid

    :param path: full path to the dataset
    :type path: str
    :raises ValueError: if the path does not contain a directory called CMIP6
    :return: the base filename structure
    :rtype: str
    """
    parts = path.strip("/").split("/")
    # print(parts)
    try:
        i = parts.index("CMIP6")
    except ValueError:
        raise ValueError("There is no CMIP6 directory in the dataset path provided") from None

    sourceid, experimentid, variantid, tableid, variableid, grid = parts[i + 3 : i + 9]

    filename_base = f"{variableid}_{tableid}_{sourceid}_{experimentid}_{variantid}_{grid}"
    return filename_base


def main():
    args = cli()
    filename_base = gen_filename_structure(args.dataset)
    print(filename_base)

    count = 0  # counter for total files
    err_count = 0
    exists_count = 0
    for year in range(1850, 2015):
        filename = f"{filename_base}_{year}01-{year}12.nc"
        filename = os.path.join(args.dataset, filename)
        if not os.path.exists(filename):
            err = cmip6_download_file(filename, 5, False)
            if err == -1:
                err_count += 1
        else:
            exists_count += 1

        count += 1

    print(f"Total files expected : {count}")
    print(f"Total files existing : {exists_count}")
    print(f"Total files failed downloading: {err_count}")
    print(f"Total files downloaded: {count - err_count - exists_count}")


if __name__ == "__main__":
    main()
