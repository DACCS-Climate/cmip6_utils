#!/usr/bin/env python
import argparse
import os
import sys
from typing import Tuple

from cmip6_utils.cli import add_common_parser_args, set_default_rootdir
from cmip6_utils.dir import CMIPDirLevels, get_cmip_directories_at_level
from cmip6_utils.historical.rule_exceptions import EC_Earth3_historical_start_year_1970


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


def check_continuity_of_intervals(files: list[str], root: str, experiment: str) -> list[int, list]:
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
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            "This program checks for inconsistencies in the data files for the provided "
            "variable for the historical experiment. Inconsistencies include, missing years "
            " ranges, incorrect start and stop years etc."
        ),
        epilog="Note: This program can be used at any stage of the CMIP6 post-processing work.",
    )
    add_common_parser_args(parser, exp=True)
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])
    set_default_rootdir(args)
    return args


def main():
    args = cli()

    for exp_root, dirs, _ in get_cmip_directories_at_level(args.rootdir, CMIPDirLevels.source):
        if args.experiment in dirs:
            for root, dirs, files in os.walk(os.path.join(exp_root, args.experiment)):
                if files:  # we have reached the bottom level
                    if f"/{args.variable}/" in root:
                        err = check_continuity_of_intervals(files, root, args.experiment)
                        errcode = err[0]
                        if errcode != 0:
                            print(root)
                            for error in err[1]:
                                if error != 0:
                                    if error[0] == -1:
                                        print(
                                            f"   {BC.fail('Discontinuity')} at year {error[1]}. Previous year was {error[2]}"
                                        )
                                    elif error[0] == -2:
                                        print(f"   {BC.warn('Start year')} is {error[1]}")
                                    elif error[0] == -3:
                                        print(f"   {BC.warn('End year')} is {error[1]}")


if __name__ == "__main__":
    main()
