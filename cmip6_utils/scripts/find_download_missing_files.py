#!/usr/bin/env python
import os
import os.path as osp
import shutil
import tempfile
import warnings
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from dataclasses import dataclass
from typing import Tuple

from esgpull import Esgpull, Query

from cmip6_utils.file import download_file
from cmip6_utils.misc import BC, verify_checksum


@dataclass
class ESGFFile:
    filename: str
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
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "dataset_path",
        type=str,
        help="Full path to the dataset directory containing the files",
    )
    args = parser.parse_args()
    args.dataset_path = args.dataset_path.rstrip("/")

    return args


def split_dataset_path(path: str) -> Tuple[str, str]:
    i = path.find("CMIP6")
    return path[:i].rstrip("/"), path[i:].strip("/")


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

    path_to_cmip6_data, cmip6_dataset_structure = split_dataset_path(args.dataset_path)
    version = dataset_version(args.dataset_path)

    # print(f"{BC.bold('Dataset path:')} {args.dataset_path}")
    print(f"{BC.bold('Local path to CMIP6 data:')} {path_to_cmip6_data}")
    print(f"{BC.bold('CMIP6 dataset structure :')} {cmip6_dataset_structure}")
    print(f"{BC.bold('Dataset version         :')} {version}")
    print("\n")

    query = cmip_path_to_query(cmip6_dataset_structure)

    print_query(query)

    query.options.distrib = True  # default=False
    query.options.replica = True

    # Currently the Esgpull class raises a useless warning.
    esg = Esgpull(path="/home/dchandan/esgpull_profiles/scratch")
    search_results = esg.context.files(query, max_hits=None)

    dataset_files = {}

    print(f"{BC.warn('# of files found from search: ')}{len(search_results)}")

    for res in search_results:
        if version == res.version:
            filename = res.filename
            data_ = (filename, res.url, res.checksum, res.local_path, res.data_node)
            if filename in dataset_files:
                dataset_files[filename].append(ESGFFile(*data_))
            else:
                dataset_files[filename] = [ESGFFile(*data_)]

    print(f"{BC.warn('# of unique files: ')}{len(dataset_files)}")

    changes_made = False
    for filename, entries in dataset_files.items():
        if not osp.exists(osp.join(args.dataset_path, filename)):
            success = False
            print(f"Found missing file: {filename}")

            tf_ = tempfile.NamedTemporaryFile()
            for item in entries:
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
                            continue

                        changes_made = True
                        break
                    else:
                        print(f" ---> Checksum {BC.fail('FAIL')}")
                else:
                    print(f" ---> Download {BC.fail('unsuccessful')}")

            if not success:
                print(f" ---> {BC.fail('Unable to download this file from any source')}")

    if not changes_made:
        print(f"{BC.warn('No missing files were found')}")


if __name__ == "__main__":
    main()
