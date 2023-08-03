#!/usr/bin/env python
"""
This script is run after the completion of esgpull download phase. The purpose of this script is to
download files that were not downloaded by esgpull.
"""
import argparse
import logging
import multiprocessing as mp
import os
import shutil
import sqlite3
import tempfile
import time
from datetime import datetime
from logging.handlers import QueueHandler
from typing import Callable
from urllib.parse import urlparse

import lxml.etree
import requests
from colorlog import ColoredFormatter

from cmip6_utils.file import download_file
from cmip6_utils.misc import verify_checksum
from cmip6_utils.parallel import MPPartition

LOGGER = logging.getLogger("MAIN")
formatter = ColoredFormatter("  %(log_color)s%(levelname)s:%(reset)s %(message)s")
stream = logging.StreamHandler()
stream.setFormatter(formatter)
LOGGER.addHandler(stream)
LOGGER.setLevel(logging.INFO)


def search_for_masterid(
    logger: logging.Logger, search_node: str, master_id: str, output_directory: str, timeout: int, ignorehosts=[]
) -> tuple:
    logger.info(f"Master ID: {master_id}")
    logger.info(f"Download location: {output_directory}")

    api = f"https://{search_node}/esg-search/search?"
    search = f"{api}type=File&distrib=true&master_id={master_id}"

    resp = requests.get(search)

    if resp.status_code != 200:
        logger.error(f"Unable to access search. Received code {resp.status_code}")
        return (False,)

    parser = lxml.etree.XMLParser(encoding="UTF-8")
    tree = lxml.etree.fromstring(resp.content, parser=parser)

    result = tree.xpath("result")[0]

    num_found = int(result.attrib["numFound"])
    logger.info(f"Found {num_found} sources of file")

    for i, urlelem in enumerate(result.xpath("doc")):
        urlelem.findall('arr[@name="checksum"]')
        cs = urlelem.findall('arr[@name="checksum"]')[0]
        cs = cs.find("str").text
        for url in urlelem.find('arr[@name="url"]').findall("str"):
            if url.text.endswith("HTTPServer"):
                url = url.text.strip().split("|")[0].strip()
                _p = urlparse(url)
                host = _p.hostname
                if host in ignorehosts:
                    logger.warn(f"Ignoring host {i + 1}: {host}")
                    break
                logger.info(f"Attempting retrieval from source {i + 1} [Host: {_p.hostname}]")

                local_filename = url.split("/")[-1]
                local_filename = os.path.join(output_directory, local_filename)
                status_code = download_file(url, local_filename, timeout=timeout)

                if status_code == 200:
                    logger.info("Download successful")
                    vrfy = verify_checksum(local_filename, cs)
                    if vrfy:
                        logger.info("Checksum PASS")
                        return (True, local_filename)
                    else:
                        logger.error("Checksum FAIL")
                else:
                    logger.error(f"Download unuccessful. Got error code {status_code}")
                    break

    return (False,)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("dbname", type=str, help="Full path to esgpull database")
    parser.add_argument("variable", type=str, help="Name of the variable whose files are in the database")
    parser.add_argument(
        "cmip6_data_dir", type=str, help="Directory where the 'CMIP6' root data directory for CMIP6 data is located"
    )
    parser.add_argument("--ignore-hosts", nargs="+", help="ESGF hosts to ignore", default=[])
    parser.add_argument("--search-node", type=str, default="esgf-node.llnl.gov", help="Search node to query")
    parser.add_argument("-n", type=int, help="Number of parallel processes", default=10)
    parser.add_argument("-t", type=int, help="Timeout (in seconds) for downloading a file", default=7)
    args = parser.parse_args()

    # All the localpaths in the database begin with CMIP6. I am checking here if there is such a directory in the
    # supplied location for such directory.
    if not os.path.exists(os.path.join(args.cmip6_data_dir, "CMIP6")):
        raise ValueError("No 'CMIP6' directory in the supplied location for CMIP6 directory.")

    return args


def listener_configurer(logfile_name: str) -> None:
    root = logging.getLogger()
    stream = logging.StreamHandler()
    formatter = ColoredFormatter("%(log_color)s%(processName)-10s %(levelname)-8s%(reset)s %(message)s")
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    root.addHandler(stream)

    fh = logging.FileHandler(logfile_name)
    fh.setFormatter(logging.Formatter("%(processName)-10s %(levelname)-8s %(message)s"))
    root.addHandler(fh)


# This is the listener process top-level loop: wait for logging events
# (LogRecords)on the queue and handle them, quit when you get a None for a
# LogRecord.
def listener_process(queue: mp.Queue, configurer: Callable, logfile_name: str) -> None:
    configurer(logfile_name)
    while True:
        try:
            record = queue.get()
            if record is None:  # We send this as a sentinel to tell the listener to quit.
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)  # No level or filter logic applied - just do it!
        except Exception:
            import sys
            import traceback

            print("Whoops! Problem:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def worker_configurer(queue: mp.Queue) -> None:
    h = QueueHandler(queue)  # Just the one handler needed
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.INFO)


def worker(
    dbname: str,
    log_queue: mp.Queue,
    configurer: Callable,
    masterids: list[str],
    localpaths: list[str],
    cmip6_data_dir: str,
    return_queue: mp.Queue,
    temp_dir: str,
    search_node: str,
    ignore_hosts: list[str],
    timeout: int,
):
    configurer(log_queue)
    name = mp.current_process().name
    logger = logging.getLogger(f"worker{name}")

    con = sqlite3.connect(dbname)
    update_cur = con.cursor()

    return_data = []

    for master_id, localpath in zip(masterids, localpaths):
        # return_data.append((False, master_id))
        downloadpath = os.path.join(temp_dir, localpath)
        os.makedirs(downloadpath, exist_ok=True)
        ret_vals = search_for_masterid(logger, search_node, master_id, downloadpath, timeout, ignore_hosts)
        successful = ret_vals[0]
        if len(ret_vals) > 1:
            local_filename = ret_vals[1]
        if not successful:
            return_data.append([False, master_id])
        else:
            localpath = os.path.join(cmip6_data_dir, localpath)
            logger.info(f"Moving downloaded file to {localpath}")
            os.makedirs(localpath, exist_ok=True)
            shutil.move(local_filename, localpath)

            _ = update_cur.execute(f"UPDATE file SET status='Done' WHERE master_id='{master_id}'")
            con.commit()
            return_data.append([True, master_id])

    con.close()

    return_queue.put(return_data)


def diagnostics(queue: mp.Queue, variable: str, totalfiles: int, nprocs: int) -> None:
    good = 0
    bad = 0
    bad_master_ids = []
    for i in range(nprocs):
        data = queue.get()
        for item in data:
            success, master_id = item

            if success:
                good += 1
            else:
                bad += 1
                bad_master_ids.append(master_id)

    print("\n\n\n")
    LOGGER.info("=======================================================================")
    LOGGER.info(f"Files that needed fixing     :  {totalfiles}")
    LOGGER.info(f"Files successfully fixed     :  {good}")
    LOGGER.info(f"Files that could not be fixed:  {bad}")
    LOGGER.info("=======================================================================\n\n\n")

    if bad > 0:
        LOGGER.info("Problematic master IDs:")
        with open(f"unfixed_master_ids_{variable}_{datetime.strftime(datetime.now(), '%Y%m%d')}.txt", "w") as f:
            for item in bad_master_ids:
                LOGGER.error(item)
                f.write(item + "\n")

    LOGGER.info(f"End time {datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')}")


def main():
    args = cli()
    logfile_name = f"{args.variable}.{datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')}.log"

    fh = logging.FileHandler(logfile_name)
    fh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    LOGGER.addHandler(fh)

    LOGGER.info(f"Start time {datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')}")
    dbname = args.dbname
    LOGGER.info(f"Using database: {dbname}")

    # backup the database first
    db_backup_name = f"{dbname}.backup{datetime.strftime(datetime.now(), '%Y%m%d')}"
    LOGGER.info(f"Backing up database to: {db_backup_name}")
    shutil.copy(dbname, db_backup_name)

    time.sleep(5)

    # Read the list of problematic files from the database
    con = sqlite3.connect(dbname)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    res = cur.execute("SELECT * from file WHERE status='Error'")
    totalfiles = len(res.fetchall())
    res = cur.execute("SELECT * from file WHERE status='Error'")

    masterids = []
    localpaths = []

    for item in res:
        masterids.append(item["master_id"])
        localpaths.append(item["local_path"])

    con.close()

    temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    logging_queue = mp.Queue(-1)
    return_queue = mp.Queue(-1)

    listener = mp.Process(target=listener_process, args=(logging_queue, listener_configurer, logfile_name))
    listener.start()

    nprocs = args.n

    # A paritioner for partitioning the input data between processes
    partitioner = MPPartition(0, totalfiles + 1, nprocs)

    processes = []

    for i in range(nprocs):
        thisStart, thisEnd, _ = partitioner.get_partition(i, printdecomp=True)
        processes.append(
            mp.Process(
                target=worker,
                args=(
                    dbname,
                    logging_queue,
                    worker_configurer,
                    masterids[thisStart:thisEnd],
                    localpaths[thisStart:thisEnd],
                    args.cmip6_data_dir,
                    return_queue,
                    temp_dir.name,
                    args.search_node,
                    args.ignore_hosts,
                    args.t,
                ),
            )
        )

    time.sleep(5)

    for p in processes:
        p.start()

    # for p in processes:
    #     p.join()

    diagnostics(return_queue, args.variable, totalfiles, nprocs)

    logging_queue.put_nowait(None)
    listener.join()


if __name__ == "__main__":
    main()
