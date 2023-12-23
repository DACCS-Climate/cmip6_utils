import os
from argparse import ArgumentParser, Namespace
from typing import Optional

from cmip6_utils.cmip6 import experiment_to_activity


def add_common_parser_args(
    parser: ArgumentParser, exp: Optional[bool] = False, adir: Optional[bool] = True, dryrun: Optional[bool] = False
) -> None:
    parser.add_argument(
        "variable",
        type=str,
        help="Name of the CMIP6 variable on which to operate",
    )

    if exp:
        parser.add_argument(
            "experiment",
            type=str,
            help="Name of the CMIP6 experiment",
            choices=["historical", "ssp245", "ssp370", "ssp585", "ssp126"],
        )

    if adir:
        # Path to the CMIP6 activity (e.g. /data/Datasets/CMIP6/ScenarioMIP, /data/Datasets/CMIP6/CMIP)
        parser.add_argument("--activitydir", "-a", type=str, help="Root directory for the CMIP6 activity.")

    if dryrun:
        parser.add_argument(
            "--dry-run",
            "-t",
            action="store_true",
            help=(
                "Do a dry run. This does not make any changes to the filesystem. "
                "This will simply print the processing it will do and then exit. Useful as a first "
                "step before making changes."
            ),
        )


def set_default_activitydir(args: Namespace):
    if not args.activitydir:
        args.activitydir = os.path.join("/data/Datasets/CMIP6", experiment_to_activity(args.experiment))
