import argparse
import os
from typing import Tuple

from cmip6_utils.historical.rule_exceptions import EC_Earth3_historical_start_year_1970
from cmip6_utils.misc import BC
from cmip6_utils.time import dates_range_from_file

# class BaseIngoreStartDate:
#     @classmethod
#     def check_ignore(cls):
#         pass


# class EC_Earth3_historical_start_year_1970(BaseIngoreStartDate):
#     # These variants start in 1970
#     variants = [
#         "r128i1p1f1",
#         "r126i1p1f1",
#         "r125i1p1f1",
#         "r144i1p1f1",
#         "r118i1p1f1",
#         "r123i1p1f1",
#         "r113i1p1f1",
#         "r129i1p1f1",
#         "r130i1p1f1",
#         "r105i1p1f1",
#         "r148i1p1f1",
#         "r106i1p1f1",
#         "r127i1p1f1",
#         "r139i1p1f1",
#         "r131i1p1f1",
#         "r145i1p1f1",
#         "r137i1p1f1",
#         "r122i1p1f1",
#         "r109i1p1f1",
#         "r135i1p1f1",
#         "r132i1p1f1",
#         "r120i1p1f1",
#         "r104i1p1f1",
#         "r147i1p1f1",
#         "r121i1p1f1",
#         "r140i1p1f1",
#         "r124i1p1f1",
#         "r138i1p1f1",
#         "r114i1p1f1",
#         "r115i1p1f1",
#         "r141i1p1f1",
#         "r110i1p1f1",
#         "r117i1p1f1",
#         "r116i1p1f1",
#         "r149i1p1f1",
#         "r108i1p1f1",
#         "r146i1p1f1",
#         "r107i1p1f1",
#         "r136i1p1f1",
#         "r150i1p1f1",
#         "r119i1p1f1",
#         "r103i1p1f1",
#         "r101i1p1f1",
#         "r112i1p1f1",
#         "r134i1p1f1",
#         "r143i1p1f1",
#         "r102i1p1f1",
#         "r111i1p1f1",
#         "r133i1p1f1",
#         "r142i1p1f1",
#     ]

#     @classmethod
#     def check_ignore(cls, dataset):
#         for variant in cls.variants:
#             if variant in dataset:
#                 return True


def years(date):
    st, ed = date.split("-")
    st = st[:4]
    ed = ed[:4]
    return int(st), int(ed)


def check_start_date(intervals: list[str], expected_start_date: str, dataset_dir: str) -> Tuple[int, int]:
    st, ed = years(intervals[0])  # the start and end years of the first interval
    if "EC-Earth-Consortium/EC-Earth3/historical" in dataset_dir:
        if EC_Earth3_historical_start_year_1970.check_ignore(dataset_dir):
            return (0, st)

    if st != expected_start_date:
        return (-2, st)
    return (0, st)


def check_end_date(intervals: list[str], expected_end_date: int) -> Tuple[int, int]:
    st, ed = years(intervals[-1])
    if ed != expected_end_date:
        return (-3, ed)
    return (0,)


def check_continuity(intervals: list[str], start_year: int):
    prev_end_year = start_year
    for period in intervals:
        st, ed = years(period)  # extract the start, end years from each interval
        if st != prev_end_year + 1:
            return (-1, st, prev_end_year)

        prev_end_year = ed
    return (0,)


def check_continuity_of_intervals(files: list[str], root: str) -> list[int, list]:
    # intervals is a sorted list of dates (e.g. "191401-191412") from the netcdf files
    intervals = sorted([file.strip().split(".")[0].split("_")[-1] for file in files])
    # print(root)
    # print("   ", len(intervals))
    ERR = [0, []]
    err = check_start_date(intervals, 1850, root)
    code = err[0]
    ERR[0] += code
    if code != 0:
        ERR[1].append(err)

    start_year = err[1] - 1

    err = check_end_date(intervals, 2014)
    code = err[0]
    ERR[0] += code
    if code != 0:
        ERR[1].append(err)

    # using the start date returned from the first check because I don't want a spurious
    # dicsontinuity error because the start date is different
    err = check_continuity(intervals, start_year)
    code = err[0]
    ERR[0] += code
    if code != 0:
        ERR[1].append(err)

    return ERR


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("variable", type=str, help="Name of the vrabiable to check")
    parser.add_argument(
        "cmip6_data_dir", type=str, help="Directory where the 'CMIP6' root data directory for CMIP6 data is located"
    )
    return parser.parse_args()


def main():
    args = cli()

    for root, _, files in os.walk(args.cmip6_data_dir):
        if files:  # we have reached the bottom level
            if f"/{args.variable}/" in root:
                err = check_continuity_of_intervals(files, root)
                errcode = err[0]
                if errcode != 0:
                    print(root)
                    for error in err[1]:
                        if error != 0:
                            if error[0] == -1:
                                print(f"   {BC.fail('Discontinuity')} at year {error[1]}. Previous year was {error[2]}")
                            elif error[0] == -2:
                                print(f"   {BC.warn('Start year')} is {error[1]}")
                            elif error[0] == -3:
                                print(f"   {BC.warn('End year')} is {error[1]}")


if __name__ == "__main__":
    main()
