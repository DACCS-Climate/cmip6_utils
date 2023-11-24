import os
import os.path as osp
from typing import Optional


def count_months(start_date: str, end_date: str) -> int:
    """
    Counts the number of months of model results between the start_date and end_date.
    Note: the months of start_date and end_date are not included in the count
    """
    start_year = int(start_date[:4])
    start_month = int(start_date[4:])

    end_year = int(end_date[:4])
    end_month = int(end_date[4:])

    months = 0

    while not ((start_year == end_year) and (start_month == end_month)):
        months += 1

        start_month = (start_month % 12) + 1

        if start_month == 1:
            start_year += 1

    return months - 1


# assert count_months("187912", "188101") == 12
# assert count_months("185001", "185012") == 10
# assert count_months("185001", "185002") == 0
# assert count_months("187912", "188012") == 11
# assert count_months("188001", "188101") == 11


def consecutive_months(d1: str, d2: str):
    y1 = int(d1[:4])
    y2 = int(d2[:4])
    m1 = int(d1[4:])
    m2 = int(d2[4:])
    m1 = m1 % 12
    m2 = m2 if m2 == 12 else m2 % 12

    if (m2 - m1) == 1:
        if y1 == y2:
            return True
        if m1 == 0:
            return y1 == y2 - 1
    else:
        return False


def dates_range_from_file(fname: str, only: Optional[str] = None) -> tuple[str, str]:
    dates = osp.basename(fname).strip().split(".")[0].split("_")[-1].split("-")
    sty = dates[0]
    edy = dates[1]
    if only:
        if only == "start":
            return sty
        elif only == "end":
            return edy
        else:
            raise ValueError("Unknown value for 'only'")
    else:
        return sty, edy


# print(years_range_from_file("blah/blah/tasmax_Amon_EC-Earth3-Veg_historical_r10i1p1f1_gr_187901-187912.nc", only="end"))
