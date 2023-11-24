#!/usr/bin/env python

"""
This script can be used to download a file. For example, if the desired local file is:

/data/Datasets/CMIP6/CMIP/MIROC/MIROC6/historical/r1i1p1f1/Amon/hurs/gn/v20181212/hurs_Amon_MIROC6_historical_r1i1p1f1_gn_195001-201412.nc

Then this script can be called to download it.
"""
import os
import os.path as osp
import shutil
import sys
import tempfile
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from dataclasses import dataclass
from typing import Optional, Tuple

from esgpull import Esgpull, Query

from cmip6_utils.file import download_file
from cmip6_utils.misc import BC, verify_checksum


@dataclass
class ESGFFile:
    url: str
    checksum: str
    local_path: str
    data_node: str


def cmip_path_to_query(path: str) -> Query:
    if not path.startswith("CMIP6"):
        raise RuntimeError("path should be described with root directory CMIP6")

    path = path.strip().split("/")

    query = Query()
    query.selection.project = path[0]
    query.selection.activity_id = path[1]
    query.selection.institution_id = path[2]
    query.selection.source_id = path[3]
    query.selection.experiment_id = path[4]
    query.selection.variant_label = path[5]
    query.selection.table_id = path[6]
    query.selection.variable_id = path[7]
    query.selection.grid_label = path[8]

    return query


def cli() -> Namespace:
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description=(
            "This script can be used to download a file. E.g. if file is "
            "/the/full/local/path/to/filename.nc. Then this script will search "
            "for filename.nc and, if available, download it to /the/full/local/path/to."
        ),
    )
    parser.add_argument("filename_with_path", type=str, help="Full local path to the file to download")
    parser.add_argument(
        "-t",
        type=int,
        help=("Timeout (in seconds) for downloading a file " "(parameter to requests.get())."),
        default=5,
    )
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])

    if not args.filename_with_path.endswith(".nc"):
        raise ValueError("The supplied argument to the program is not a netCDF file")
    return args


def parse_file_path(path: str) -> Tuple[str, str]:
    tokens = path.rpartition("/")
    basename = tokens[0]
    filename = tokens[2]
    i = basename.find("CMIP6")
    return basename[:i].rstrip("/"), basename[i:].strip("/"), filename


def get_dataset_version(path: str) -> str:
    version = path.strip().split("/")[-1]
    assert version.startswith("v")
    return version


def print_query(query: Query):
    print(BC.bold("Query selection:"))
    for facet in query.selection._facets:
        print(f"{facet.name:15s}: {facet.value}")
    print("\n")


def main():
    args = cli()
    cmip6_download_file(args.filename_with_path, args.t)


def cmip6_download_file(filename_with_path: str, t: int, verbose: Optional[bool] = True):
    path_to_cmip6_data, cmip6_dataset_structure, filename = parse_file_path(filename_with_path)
    print(path_to_cmip6_data, cmip6_dataset_structure, filename)
    version = get_dataset_version(cmip6_dataset_structure)

    # print(f"{BC.bold('Dataset path:')} {filename_with_path}")
    print(f"{BC.bold('Local path to CMIP6 data:')} {path_to_cmip6_data}")
    print(f"{BC.bold('CMIP6 dataset structure :')} {cmip6_dataset_structure}")
    print(f"{BC.bold('Required filename       :')} {filename}")
    print(f"{BC.bold('Dataset version         :')} {version}")
    print("\n")

    query = cmip_path_to_query(cmip6_dataset_structure)

    if verbose:
        print_query(query)

    query.options.distrib = True  # default=False
    query.options.replica = True

    # Currently the Esgpull class raises a useless warning.
    # with warnings.catch_warnings():
    # warnings.simplefilter("ignore")
    esg = Esgpull(path="/home/dchandan/esgpull_profiles/scratch")
    search_results = esg.context.files(query, max_hits=None)

    file_urls = []

    print(f"{BC.warn('# of files found from search: ')}{len(search_results)}")

    for res in search_results:
        if version == res.version:
            if res.filename == filename:
                data_ = (res.url, res.checksum, res.local_path, res.data_node)
                file_urls.append(ESGFFile(*data_))

    print(f"{BC.warn('# of entries found for the file: ')}{len(file_urls)}")

    success = False
    for item in file_urls:
        tf_ = tempfile.NamedTemporaryFile()
        print(f" ---> Attempting download from: {item.data_node}")
        err = download_file(item.url, tf_.name, timeout=t)

        if err == 200:
            print(f" ---> Download {BC.okgreen('successful')}")
            vrfy = verify_checksum(tf_.name, item.checksum)
            if vrfy:
                print(f" ---> Checksum {BC.okgreen('PASS')}")
                success = True
                localpath = osp.join(path_to_cmip6_data, item.local_path)
                print(f" ---> Copying downloaded file to {localpath}")
                os.makedirs(localpath, exist_ok=True)
                local_filename = osp.join(localpath, filename)
                shutil.copy2(tf_.name, local_filename)
                vrfy2 = verify_checksum(local_filename, item.checksum)
                if not vrfy2:
                    print(f" ---> {BC.fail('Checksum of copied file failed')}")
                    os.remove(local_filename)
                    success = False
                else:
                    break
            else:
                print(f" ---> Checksum {BC.fail('FAIL')}")
        else:
            print(f" ---> Download {BC.fail('unsuccessful')}")

    if not success:
        print(f" ---> {BC.fail('Unable to download this file from any source')}")
        return -1
    else:
        return 0


if __name__ == "__main__":
    main()
