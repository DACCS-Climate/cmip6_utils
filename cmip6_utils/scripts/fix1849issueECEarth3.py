import argparse
import glob
import os
import sys

from netCDF4 import Dataset

from cmip6_utils.nchelpers import (
    bulk_copy_variable_data,
    copy_dimension_definitions,
    copy_file_metadata,
    copy_variable_definitions,
)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("variable", type=str, help="Name of the vrabiable to check")
    parser.add_argument(
        "path",
        type=str,
        help="Directory to the location with file starting in year 1849",
    )
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])

    os.chdir(args.path)
    file = glob.glob("*184912*nc")
    assert len(file) == 1
    file = file[0]
    print(f"Problematic file: {file}")

    ofname = file.replace("184912", "185001")
    print(f"Creating output file: {ofname}")

    oncf = Dataset(ofname, "w", format="NETCDF4")
    ncf = Dataset(file, "r")

    copy_dimension_definitions(ncf, oncf)
    copy_variable_definitions(ncf, oncf)
    copy_file_metadata(oncf, ncf.__dict__)

    time_vars = ["time", "time_bnds", args.variable]
    bulk_copy_variable_data(ncf, oncf, exclude=time_vars)

    for var_name in time_vars:
        ovar = oncf[var_name]
        ivar = ncf[var_name]
        ovar[:, ...] = ivar[1:, ...]

    oncf.close()
    ncf.close()

    os.remove(file)


if __name__ == "__main__":
    main()
