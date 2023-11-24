import logging
import shutil
import time
from typing import Optional

import requests
from colorlog import ColoredFormatter
from urllib3.exceptions import ReadTimeoutError

LOGGER = logging.getLogger("MAIN")
# formatter = ColoredFormatter("  %(log_color)s%(levelname)s:%(reset)s %(message)s")
# stream = logging.StreamHandler()
# stream.setFormatter(formatter)
# LOGGER.addHandler(stream)
LOGGER.setLevel(logging.INFO)


def download_file(url: str, local_filename: str, timeout: Optional[int] = 5) -> int:
    read_counter = 0
    break_read_error_loop = False

    while (not break_read_error_loop) and (read_counter < 5):
        count = 0
        break_connection_error_loop = False
        while (not break_connection_error_loop) and (count < 5):
            try:
                resp = requests.get(url, stream=True, timeout=timeout)
                status_code = resp.status_code
            except requests.exceptions.ReadTimeout:
                LOGGER.warn("ReadTimeout from cmip6_utils.file.download_file")
                status_code = 408
            except requests.exceptions.ConnectTimeout:
                LOGGER.warn("ConnectTimeout from cmip6_utils.file.download_file")
                status_code = 408
            except requests.exceptions.ConnectionError:
                LOGGER.warn("ConnectionError from cmip6_utils.file.download_file")
                status_code = 491
            except Exception:
                LOGGER.warn("Unknown error from cmip6_utils.file.download_file")
                status_code = 499

            if status_code != 200:
                count += 1
                LOGGER.warn(f"Failed opening URL.... Retrying {count}")
                time.sleep(5)
            else:
                break_connection_error_loop = True

        if count == 5:
            break_read_error_loop = True

        if status_code == 200:
            try:
                with open(local_filename, "wb") as f:
                    shutil.copyfileobj(resp.raw, f)
                break_read_error_loop = True
            except ReadTimeoutError:
                read_counter += 1
                LOGGER.warn(f"Reading from stream failed.... Retrying {read_counter}")
                status_code = -1
                time.sleep(5)

    return status_code
