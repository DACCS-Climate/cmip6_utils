import os
from argparse import ArgumentParser, Namespace
from typing import Optional

from cmip6_utils.cmip6 import experiment_to_activity


def add_common_parser_args(
    parser: ArgumentParser,
    exp: Optional[bool] = False,
) -> None:
    parser.add_argument(
        "variable",
        type=str,
        help="Name of the CMIP6 variable for which to download files",
    )

    # parser.add_argument(
    #     "--rootdir",
    #     "-d",
    #     type=str,
    #     default="/data/Datasets",
    #     help="Root directory for CMIP6 data. The directory must have a 'CMIP6' folder.",
    # )
    if exp:
        parser.add_argument(
            "experiment",
            type=str,
            help="Name of the experiment",
            choices=["historical", "ssp245", "ssp370", "ssp585", "ssp126"],
        )

    # Path to the CMIP6 activity (e.g. /data/Datasets/CMIP6/ScenarioMIP, /data/Datasets/CMIP6/CMIP)
    parser.add_argument("--activitydir", "-a", type=str, help="Root directory for the CMIP6 activity.")


def set_default_activitydir(args: Namespace):
    if not args.activitydir:
        args.activitydir = os.path.join("/data/Datasets/CMIP6", experiment_to_activity(args.experiment))
