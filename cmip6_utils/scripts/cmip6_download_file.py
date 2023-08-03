#!/usr/bin/env python
import os
import os.path as osp
import shutil
import tempfile
import warnings
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from typing import Tuple

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
    parser = ArgumentParser()
    parser.add_argument("dataset_path", type=str, help="Full path to the dataset directory containing the files")
    args = parser.parse_args()
    args.dataset_path = args.dataset_path.rstrip("/")

    return args


def parse_file_path(path: str) -> Tuple[str, str]:
    tokens = path.rpartition("/")
    basename = tokens[0]
    filename = tokens[2]
    i = basename.find("CMIP6")
    return basename[:i].rstrip("/"), basename[i:].strip("/"), filename


def dataset_version(path: str) -> str:
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

    path_to_cmip6_data, cmip6_dataset_structure, filename = parse_file_path(args.dataset_path)
    # print(path_to_cmip6_data, cmip6_dataset_structure, filename)
    version = dataset_version(cmip6_dataset_structure)

    # print(f"{BC.bold('Dataset path:')} {args.dataset_path}")
    print(f"{BC.bold('Local path to CMIP6 data:')} {path_to_cmip6_data}")
    print(f"{BC.bold('CMIP6 dataset structure :')} {cmip6_dataset_structure}")
    print(f"{BC.bold('Required filename       :')} {filename}")
    print(f"{BC.bold('Dataset version         :')} {version}")
    print("\n")

    query = cmip_path_to_query(cmip6_dataset_structure)

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
            # print(res.filename)
            if res.filename == filename:
                data_ = (res.url, res.checksum, res.local_path, res.data_node)
                file_urls.append(ESGFFile(*data_))

    print(f"{BC.warn('# of entries found for the file: ')}{len(file_urls)}")

    success = False
    for item in file_urls:
        tf_ = tempfile.NamedTemporaryFile()
        print(f" ---> Attempting download from: {item.data_node}")
        err = download_file(item.url, tf_.name)

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
                    # break
            else:
                print(f" ---> Checksum {BC.fail('FAIL')}")
        else:
            print(f" ---> Download {BC.fail('unsuccessful')}")

    if not success:
        print(f" ---> {BC.fail('Unable to download this file from any source')}")


if __name__ == "__main__":
    main()
