import argparse
import datetime
import os
import os.path as osp
import shutil
import sys
import tempfile

from netCDF4 import Dataset

from cmip6_utils.historical.rule_exceptions import EC_Earth3_historical_start_year_1970
from cmip6_utils.misc import BC
from cmip6_utils.nchelpers import (
    bulk_copy_variable_data,
    copy_dimension_definitions,
    copy_file_metadata,
    copy_variable_definitions,
)
from cmip6_utils.time import count_months, dates_range_from_file


def make_output_file_name(first_file: str, last_file: str) -> str:
    """Make the output filename based on the names of the first and last files in the collection.

    :param first_file: name of the first file
    :type first_file: str
    :param last_file: name of the last file
    :type last_file: str
    :return: new filename
    :rtype: str
    """
    base = first_file[: first_file.rfind("_") + 1]
    sty = first_file.strip().split(".")[0].split("_")[-1].split("-")[0]
    edy = last_file.strip().split(".")[0].split("_")[-1].split("-")[1]

    return f"{base}{sty}-{edy}.nc"


def copy_reference_file(reffile: str, ofile: str, offset: int):
    """Copies the input netcdf file (with modifications) to a new file.

    :param reffile: name of file to be copied
    :type reffile: str
    :param ofile: name of the new duplicate file
    :type ofile: str
    """
    print(f"        ---> Copying first file: {osp.basename(reffile)}")
    refnc = Dataset(reffile, "r")
    oncf = Dataset(ofile, "w", format="NETCDF4")

    copy_dimension_definitions(refnc, oncf)
    copy_variable_definitions(refnc, oncf)
    metadata = refnc.__dict__

    for key in ["tracking_id", "history"]:
        if key in metadata.keys():
            _ = metadata.pop(key)

    date = datetime.datetime.ctime(datetime.datetime.now())
    metadata[
        "history"
    ] = f"This file was generated on {date} by combining two or more individual files for this dataset."

    copy_file_metadata(oncf, metadata)

    bulk_copy_variable_data(refnc, oncf, time_offset=offset)

    refnc.close()
    oncf.close()


def get_time_vars(oncf: Dataset) -> list[str]:
    """Get names of variables that have time in their dimension.

    :param oncf: open netcdf file handle. Ideally for the output file
    :type oncf: Dataset
    :return: list of time dependent variable names
    :rtype: list[str]
    """
    time_vars = []
    for var in oncf.variables:
        if "time" in oncf[var].dimensions:
            time_vars.append(var)

    return time_vars


def check_linearity(fname: str) -> bool:
    ncf = Dataset(fname, "r")
    time = ncf.variables["time"][:]
    ncf.close()

    return all(x < y for x, y in zip(time, time[1:]))


def get_start_month(fname):
    # registered_exceptions = [EC_Earth3_historical_start_year_1970]

    if "EC-Earth-Consortium/EC-Earth3/historical" in fname:
        if EC_Earth3_historical_start_year_1970.check_ignore(fname):
            return "196912"

    return "184912"


def combine_files(files: list[str], ofname: str, dry_run: bool):
    reffile = files[0]

    # Will use it to track the running end date of the newly created file
    running_edy = dates_range_from_file(reffile, only="end")

    status = 0

    first_file_start_date = dates_range_from_file(reffile, only="start")
    expected_start_month = get_start_month(reffile)
    # print(expected_start_month)
    months_offset = count_months(expected_start_month, first_file_start_date)
    start_year = int(expected_start_month[:4]) + 1
    if months_offset > 0:
        print(
            BC.fail(
                f"Discontinuity of {months_offset} months at the start of time series."
            )
        )
        print(BC.fail(f"First file is: {osp.basename(reffile)}"))
        print(BC.fail(f"Appending contents of first file at offset {months_offset}"))
    else:
        print(
            f"Time series will start at index {months_offset} corresponding to year {start_year}"
        )

    if not dry_run:
        # first step is to duplicate the first file
        copy_reference_file(reffile, ofname, months_offset)

        oncf = Dataset(ofname, "a")
        time_vars = get_time_vars(oncf)
        ovars = [[varname, oncf[varname]] for varname in time_vars]

        stidx = len(oncf.dimensions["time"])

    # __import__("IPython").embed()
    # sys.exit()

    # Now going through all the remaining files and appending them to the newly copied file
    for file in files[1:]:
        this_file_sty, this_file_edy = dates_range_from_file(file)
        months_offset = count_months(running_edy, this_file_sty)
        # if not consecutive_months(global_edy, sty):
        # offset = count_months(global_edy, sty)
        if months_offset != 0:
            print(
                BC.fail(
                    f"Discontinuity of {months_offset} months between {running_edy} and {this_file_sty}."
                )
            )
            print(BC.fail(f"Incrementing stidx by {months_offset}"))
            status = 1
            if not dry_run:
                stidx += months_offset

        if not dry_run:
            ncf = Dataset(file, "r")
            tlen = len(ncf.dimensions["time"])
            edidx = stidx + tlen
            print(
                f"        ---> Appending file: {osp.basename(file)} from IDX {stidx} to {edidx}"
            )

            for varname, ovar in ovars:
                ovar[stidx:edidx] = ncf[varname][:]

            stidx += tlen

        running_edy = this_file_edy

    if not dry_run:
        oncf.close()
        linearity = check_linearity(ofname) if status != 1 else True
        # linearity = check_linearity(ofname)
        if linearity:
            print("        ---> Joining files successful")

    return status


def delete_move_files(main_dir: str, tseries_fname: str):
    """Deletes the original individual files and moves the newly created single
    file to the correct location.

    :param main_dir: CMIP6 location for the files for that dataset that is being processed
    :type main_dir: str
    :param tseries_fname: full path and name of the newly created timeseries file
    :type tseries_fname: str
    """
    # 1. remove all files in the CMIP directory
    print("        ---> Removing original files")
    for file in os.listdir(main_dir):
        os.remove(osp.join(main_dir, file))

    # 2. Move new time series file to CMIP directory
    print("        ---> Moving newly created file to original directory")
    shutil.move(tseries_fname, main_dir)


def cli():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("variable", type=str, help="Name of the vrabiable to check")
    parser.add_argument(
        "--root_dir",
        "-r",
        type=str,
        default="/data/Datasets",
        help=(
            "Directory where the 'CMIP6' root data directory for CMIP6 data is located. "
            "Defaults to /data/Datasets."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Dry run. Does not combine files and does not make any modifications on the disk. "
            "This will simply print the processing it will do and then exit. Useful as a first "
            "step before making changes."
        ),
    )
    parser.add_argument(
        "--combine-only",
        action="store_true",
        help="Combine files only. Don't move it from the temporary directory to original directory.",
    )

    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])

    # All the localpaths in the database begin with CMIP6. I am checking here if there is such a directory in the
    # supplied location for such directory.
    if not osp.exists(osp.join(args.root_dir, "CMIP6")):
        raise ValueError(
            "No 'CMIP6' directory in the supplied location for CMIP6 directory."
        )

    return args


def main():
    args = cli()
    dry_run = args.dry_run
    combine_only = args.combine_only

    total_datasets_to_combine = 0
    datasets_not_needing_changes = 0
    list_of_datasets_not_needing_changes = []

    temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    odir = temp_dir.name

    for root, dirs, files in os.walk(args.root_dir):
        if files:  # we have reached the bottom level
            files = sorted(files)
            nfiles = len(files)
            if f"/{args.variable}/" in root:  # filter by variable name
                if nfiles > 1:
                    total_datasets_to_combine += 1
                    print(f"Processing: {root}")
                    print(f"    ---> Files to combine: {len(files)}")
                    print(f"    ---> Output dir is: {odir}")
                    output_file_name = make_output_file_name(files[0], files[-1])
                    print(f"    ---> Output filename: {output_file_name}")

                    files = [osp.join(root, f) for f in files]
                    output_file_name = osp.join(odir, output_file_name)
                    combine_files(files, output_file_name, dry_run)

                    if not dry_run:
                        if not combine_only:
                            delete_move_files(root, output_file_name)

                else:
                    list_of_datasets_not_needing_changes.append(
                        osp.join(root, files[0])
                    )
                    datasets_not_needing_changes += 1

    if datasets_not_needing_changes > 0:
        print("Datasets that did not need combining:")
        for item in list_of_datasets_not_needing_changes:
            print(item)

    print(f"Total datasets that needed combining  : {total_datasets_to_combine}")
    print(f"Total datasets that were already good : {datasets_not_needing_changes}")


if __name__ == "__main__":
    main()
