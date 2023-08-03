#!/usr/bin/env python
"""
This script is run after the completion of esgpull download phase. The purpose of this script is to
download files that were not downloaded by esgpull.
"""

import argparse
import hashlib
import logging
import os
import shutil
import sqlite3
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

# def verify_checksum(fname: str, refchecksum: str) -> bool:
#     checksum = hashlib.sha256(open(fname, "rb").read()).hexdigest()
#     return checksum == refchecksum


# def download_file(url: str, local_filename: str) -> int:
#     resp = requests.get(url, stream=True)

#     if resp.status_code == 200:
#         with open(local_filename, "wb") as f:
#             shutil.copyfileobj(resp.raw, f)

#     return resp.status_code


def search_for_masterid(search_node: str, master_id: str, output_directory: str, ignorehosts=[]) -> tuple:
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
                print(url)
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
                        return (True, local_filename)
                    else:
                        LOGGER.error("Checksum FAIL")
                else:
                    LOGGER.error(f"Download unuccessful. Got error code {status_code}")
                    # LOGGER.error(f"Failed URL: {url}")
                    break

    return (False,)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dbname", type=str, help="Full path to esgpull database")
    parser.add_argument("variable", type=str, help="Name of the variable whose files are in the database")
    parser.add_argument(
        "cmip6_data_dir", type=str, help="Directory where the 'CMIP6' root data directory for CMIP6 data is located"
    )
    parser.add_argument("--ignore-hosts", nargs="+", help="ESGF hosts to ignore", default=[])
    parser.add_argument("--search-node", type=str, default="esgf-node.llnl.gov", help="Search node to query")
    args = parser.parse_args()

    # All the localpaths in the database begin with CMIP6. I am checking here if there is such a directory in the
    # supplied location for such directory.
    if not os.path.exists(os.path.join(args.cmip6_data_dir, "CMIP6")):
        raise ValueError("No 'CMIP6' directory in the supplied location for CMIP6 directory.")

    # attach a file handler based on the arguments provided
    fh = logging.FileHandler(f"{args.variable}.{datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')}.log")
    fh.setFormatter(logging.Formatter("  %(levelname)s: %(message)s"))
    LOGGER.addHandler(fh)

    LOGGER.info(f"Start time {datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')}")
    dbname = args.dbname
    LOGGER.info(f"Using database: {dbname}")

    # backup the database first
    db_backup_name = f"{dbname}.backup{datetime.strftime(datetime.now(), '%Y%m%d')}"
    LOGGER.info(f"Backing up database to: {db_backup_name}")
    shutil.copy(dbname, db_backup_name)

    con = sqlite3.connect(dbname)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    update_cur = con.cursor()
    res = cur.execute("SELECT * from file WHERE status='Error'")

    totalfiles = len(res.fetchall())

    res = cur.execute("SELECT * from file WHERE status='Error'")

    problem_ids = []

    temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)

    count = 0
    good = 0
    bad = 0
    for item in res:
        master_id = item["master_id"]
        localpath = item["local_path"]  # CMIP6/CMIP/....
        downloadpath = os.path.join(temp_dir.name, localpath)
        os.makedirs(downloadpath, exist_ok=True)
        ret_vals = search_for_masterid(args.search_node, master_id, downloadpath, args.ignore_hosts)
        successful = ret_vals[0]
        if len(ret_vals) > 1:
            local_filename = ret_vals[1]
        if not successful:
            bad += 1
            problem_ids.append(master_id)
        else:
            good += 1
            localpath = os.path.join(args.cmip6_data_dir, localpath)
            LOGGER.info(f"Moving downloaded file to {localpath}")
            os.makedirs(localpath, exist_ok=True)
            shutil.move(local_filename, localpath)

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
        with open(f"unfixed_master_ids_{args.variable}_{datetime.strftime(datetime.now(), '%Y%m%d')}.txt", "w") as f:
            for item in problem_ids:
                LOGGER.info(item)
                f.write(item + "\n")

    LOGGER.info(f"End time {datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
