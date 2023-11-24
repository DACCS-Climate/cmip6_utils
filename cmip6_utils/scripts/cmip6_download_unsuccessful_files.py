#!/usr/bin/env python
"""
This script is run after the completion of esgpull download phase. The purpose of this script is to
download files that were not downloaded by esgpull.
"""

import argparse
import hashlib
import logging
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime
from urllib.parse import urlparse

import lxml.etree
import requests
from colorlog import ColoredFormatter

LOGGER = logging.getLogger("MAIN")
formatter = ColoredFormatter("  %(log_color)s%(levelname)s:%(reset)s %(message)s")
stream = logging.StreamHandler()
stream.setFormatter(formatter)
LOGGER.addHandler(stream)
LOGGER.setLevel(logging.INFO)

from cmip6_utils.file import download_file
from cmip6_utils.misc import verify_checksum


def search_and_download(search_node: str, master_id: str, output_directory: str, ignorehosts=[]) -> tuple:
    """This function queries the ESGF search API to find the files missing for the masterid and downloads them.

    :param search_node: _description_
    :type search_node: str
    :param master_id: _description_
    :type master_id: str
    :param output_directory: _description_
    :type output_directory: str
    :param ignorehosts: _description_, defaults to []
    :type ignorehosts: list, optional
    :return: _description_
    :rtype: tuple
    """
    LOGGER.info(f"Master ID: {master_id}")
    LOGGER.info(f"Download location: {output_directory}")

    api = f"https://{search_node}/esg-search/search?"
    search = f"{api}type=File&distrib=true&master_id={master_id}"

    resp = requests.get(search)

    if resp.status_code != 200:
        LOGGER.error(f"Unable to access search. Received code {resp.status_code}")
        return (False,)

    parser = lxml.etree.XMLParser(encoding="UTF-8")
    tree = lxml.etree.fromstring(resp.content, parser=parser)

    result = tree.xpath("result")[0]

    num_found = int(result.attrib["numFound"])
    LOGGER.info(f"Found {num_found} sources of file")

    for i, urlelem in enumerate(result.xpath("doc")):
        urlelem.findall('arr[@name="checksum"]')
        cs = urlelem.findall('arr[@name="checksum"]')[0]
        cs = cs.find("str").text
        for url in urlelem.find('arr[@name="url"]').findall("str"):
            if url.text.endswith("HTTPServer"):
                url = url.text.strip().split("|")[0].strip()
                # print(url)
                _p = urlparse(url)
                host = _p.hostname
                if host in ignorehosts:
                    LOGGER.warn(f"Ignoring host {i + 1}: {host}")
                    break
                LOGGER.info(f"Attempting retrieval from source {i + 1} [Host: {_p.hostname}]")
                LOGGER.info(f"URL: {url}")

                local_filename = url.split("/")[-1]
                local_filename = os.path.join(output_directory, local_filename)
                status_code = download_file(url, local_filename)

                if status_code == 200:
                    LOGGER.info("Download successful")
                    vrfy = verify_checksum(local_filename, cs)
                    if vrfy:
                        LOGGER.info("Checksum PASS")
                        return (True, num_found, local_filename)
                    else:
                        LOGGER.error("Checksum FAIL")
                        (False, num_found)
                else:
                    LOGGER.error(f"Download unuccessful. Got error code {status_code}")
                    # LOGGER.error(f"Failed URL: {url}")
                    break

    return (False, num_found)


def main():
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
        "dbname",
        type=str,
        help=(
            "Full path to esgpull database with information "
            "on files available for the variable and the files that "
            "remain to be downloaded."
        ),
    )
    parser.add_argument(
        "--rootdir",
        "-d",
        type=str,
        default="/data/Datasets",
        help="Root directory for CMIP6 data. The directory must have a 'CMIP6' folder.",
    )

    parser.add_argument("--ignore-hosts", nargs="+", help="ESGF hosts to ignore", default=[])
    parser.add_argument(
        "--search-node",
        type=str,
        default="esgf-node.llnl.gov",
        help="Search node to query. Defaults to LLNL node.",
    )
    parser.add_argument("--retry", "-r", type=str)
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])

    # All the localpaths in the database begin with CMIP6. I am checking here if there is such a directory in the
    # supplied location for such directory.
    if not os.path.exists(os.path.join(args.rootdir, "CMIP6")):
        raise ValueError("No 'CMIP6' directory in the supplied location for CMIP6 directory.")

    # attach a file handler to the logger based on the arguments to the program
    fh = logging.FileHandler(f"{args.variable}.{datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')}.log")
    fh.setFormatter(logging.Formatter("  %(levelname)s: %(message)s"))
    LOGGER.addHandler(fh)

    LOGGER.info(f"Start time {datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')}")

    if args.retry:
        with open(args.retry, "r") as of:
            input_retry_ids = []
            for line in of:
                input_retry_ids.append(line.strip())
    else:
        input_retry_ids = []

    dbname = args.dbname
    LOGGER.info(f"Using database: {dbname}")

    # This program modifies the databse. So, first backup the database in case there are issues.
    db_backup_name = f"{dbname}.backup{datetime.strftime(datetime.now(), '%Y%m%d')}"
    LOGGER.info(f"Backing up database to: {db_backup_name}")
    shutil.copy(dbname, db_backup_name)

    con = sqlite3.connect(dbname)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    update_cur = con.cursor()
    # res = cur.execute("SELECT * from file WHERE status='Error'")
    res = cur.execute("SELECT * from file WHERE status!='Done'")

    totalfiles = len(res.fetchall())

    # res = cur.execute("SELECT * from file WHERE status='Error'")
    res = cur.execute("SELECT * from file WHERE status!='Done'")

    problem_ids = []
    retry_ids = []

    temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)

    count = 0
    good = 0
    bad = 0
    for item in res:
        master_id = item["master_id"]
        localpath = item["local_path"]  # CMIP6/.../....
        # print(localpath)
        downloadpath = os.path.join(temp_dir.name, localpath)
        os.makedirs(downloadpath, exist_ok=True)
        if input_retry_ids:
            if not master_id in input_retry_ids:
                count += 1
                problem_ids.append(master_id)
                continue
        ret_vals = search_and_download(args.search_node, master_id, downloadpath, args.ignore_hosts)
        successful = ret_vals[0]
        num_found = ret_vals[1]
        if len(ret_vals) > 2:
            local_filename = ret_vals[2]

        if not successful:
            bad += 1
            problem_ids.append(master_id)
            if num_found != 0:
                retry_ids.append(master_id)
        else:
            good += 1
            localpath = os.path.join(args.rootdir, localpath)
            LOGGER.info(f"Moving downloaded file to {localpath}")
            os.makedirs(localpath, exist_ok=True)
            # shutil.move(local_filename, localpath)
            shutil.move(local_filename, os.path.join(localpath, local_filename.split("/")[-1]))

            _ = update_cur.execute(f"UPDATE file SET status='Done' WHERE master_id='{master_id}'")
            con.commit()

        count += 1
        LOGGER.info(f"Completed [{count}/{totalfiles}]")

    con.close()
    temp_dir.cleanup()

    LOGGER.info("/n/n/n")
    LOGGER.info("=======================================================================")
    LOGGER.info(f"Attempted to fix {totalfiles} files")
    LOGGER.info(f"Successfully fixed {good} files")
    LOGGER.info(f"Error fixing {bad} files")

    if bad > 0:
        LOGGER.info("Problematic master IDs:")
        with open(
            f"unfixed_master_ids_{args.variable}_{datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')}.txt",
            "w",
        ) as f:
            for item in problem_ids:
                LOGGER.info(item)
                f.write(item + "\n")

        with open(
            f"retry_unfixed_master_ids_{args.variable}_{datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')}.txt",
            "w",
        ) as f:
            for item in retry_ids:
                f.write(item + "\n")

    LOGGER.info(f"End time {datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
