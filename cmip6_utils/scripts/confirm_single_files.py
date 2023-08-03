import argparse
import os

from cmip6_utils.dir import CMIPDirLevels, get_cmip_directories_at_level

# TODO: Make it so that the experiemnt can also be specified

# def main():
#     parser = argparse.ArgumentParser(
#         description=(
#             "Check the CMIP data directory that all bottom level directories "
#             "for the supplied variable only contain single files"
#         )
#     )
#     parser.add_argument("variable", type=str, help="Name of the vrabiable to check")
#     parser.add_argument("root_dir", type=str, help="Root directory for CMIP data. Must end in 'CMIP'.")
#     args = parser.parse_args()

#     if not args.root_dir.endswith("CMIP"):
#         raise ValueError("the root directory must end with 'CMIP'")

#     num_datasets = 0
#     for root, dirs, files in os.walk(args.root_dir):
#         if files:  # we have reached the bottom level
#             nfiles = len(files)
#             if f"/{args.variable}/" in root:
#                 num_datasets += 1
#                 assert nfiles == 1

#     print(f"Total datasets checked  : {num_datasets}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Check the CMIP data directory that all bottom level directories "
            "for the supplied variable only contain single files"
        )
    )
    parser.add_argument("variable", type=str, help="Name of the vrabiable to check")
    parser.add_argument("root_dir", type=str, help="Root directory for CMIP data. Must end in 'CMIP'.")
    args = parser.parse_args()

    experiment = "historical"

    if not args.root_dir.endswith("CMIP"):
        raise ValueError("the root directory must end with 'CMIP'")

    num_datasets = 0
    for exp_root, dirs, _ in get_cmip_directories_at_level(args.root_dir, CMIPDirLevels.source):
        if experiment in dirs:
            for root, dirs, files in os.walk(os.path.join(exp_root, experiment)):
                if files:  # we have reached the bottom level
                    nfiles = len(files)
                    if f"/{args.variable}/" in root:
                        num_datasets += 1
                        assert nfiles == 1

    print(f"Total datasets checked  : {num_datasets}")


if __name__ == "__main__":
    main()
