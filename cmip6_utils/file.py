import shutil
from typing import Optional

import requests

# def download_file(url: str, local_filename: str, timeout: Optional[int] = 5) -> int:
#     try:
#         resp = requests.get(url, stream=True, timeout=timeout)
#     except requests.exceptions.ReadTimeout:
#         print("ReadTimeout from cmip6_utils.file.download_file")
#         return 408
#     except requests.exceptions.ConnectTimeout:
#         print("ConnectTimeout from cmip6_utils.file.download_file")
#         return 408
#     except requests.exceptions.ConnectionError:
#         print("ConnectionError from cmip6_utils.file.download_file")
#         return 491
#     except Exception:
#         print("Unknown error from cmip6_utils.file.download_file")
#         return 499

#     if resp.status_code == 200:
#         with open(local_filename, "wb") as f:
#             shutil.copyfileobj(resp.raw, f)

#     return resp.status_code


def download_file(url: str, local_filename: str, timeout: Optional[int] = 5) -> int:
    try:
        resp = requests.get(url, stream=True, timeout=timeout)
    except requests.exceptions.ReadTimeout:
        print("ReadTimeout from cmip6_utils.file.download_file")
        return 408
    except requests.exceptions.ConnectTimeout:
        print("ConnectTimeout from cmip6_utils.file.download_file")
        return 408
    except requests.exceptions.ConnectionError:
        print("ConnectionError from cmip6_utils.file.download_file")
        return 491
    except Exception:
        print("Unknown error from cmip6_utils.file.download_file")
        return 499

    if resp.status_code == 200:
        with open(local_filename, "wb") as f:
            shutil.copyfileobj(resp.raw, f)

    return resp.status_code
