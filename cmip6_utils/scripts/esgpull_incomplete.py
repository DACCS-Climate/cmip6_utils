from esgpull import Esgpull, Query

# Baseline test. # WORKS
# query = Query()
# query.selection.project = "CMIP6"
# query.options.distrib = True  # default=False
# esg = Esgpull(path="/home/dchandan/scratch/blah", install=True)
# nb_datasets = esg.context.hits(query, file=False)[0]
# nb_files = esg.context.hits(query, file=True)[0]
# datasets = esg.context.datasets(query, max_hits=5)
# print(f"Number of CMIP6 datasets: {nb_datasets}")
# print(f"Number of CMIP6 files: {nb_files}")
# for dataset in datasets:
#     print(dataset)

# Fine grained test CMIP6/CMIP/EC-Earth-Consortium/EC-Earth3-Veg/historical/r10i1p1f1/Amon/tas/gr/v20210523


def cmip_path_to_query(path: str) -> Query:
    if not path.startswith("CMIP6"):
        raise RuntimeError("path should be described with root directory CMIP6")

    path = path.strip().split("/")

    query = Query()
    query.selection.project = path[0]
    query.selection.activity_id = path[1]
    query.selection.institution_id = path[2]
    query.selection.source_id = path[3]
    query.selection.experiment_id = path[4]
    query.selection.variant_label = path[5]
    query.selection.table_id = path[6]
    query.selection.variable_id = path[7]
    query.selection.grid_label = path[8]

    return query


# query = cmip_path_to_query("CMIP6/CMIP/EC-Earth-Consortium/EC-Earth3-Veg/historical/r10i1p1f1/Amon/tas/gr/v20210523")
# query = cmip_path_to_query("CMIP6/CMIP/AWI/AWI-ESM-1-1-LR/historical/r1i1p1f1/Amon/tasmin/gn/v20200212")

# query.options.distrib = True  # default=False
# query.options.replica = True
# esg = Esgpull(path="/home/dchandan/scratch/blah", install=True)
# nb_datasets = esg.context.hits(query, file=False)[0]
# nb_files = esg.context.hits(query, file=True)[0]
# datasets = esg.context.datasets(query, max_hits=5)
# print(f"Number of datasets: {nb_datasets}")
# print(f"Number of files: {nb_files}")
# for dataset in datasets:
#     print(dataset)


query = cmip_path_to_query("CMIP6/CMIP/EC-Earth-Consortium/EC-Earth3-AerChem/historical/r4i1p1f1/Amon/psl/gr/v20201214")

missing_file = "psl_Amon_EC-Earth3-AerChem_historical_r4i1p1f1_gr_189301-189312.nc"

query.options.distrib = True  # default=False
query.options.replica = True
esg = Esgpull(path="/home/dchandan/esgpull_profiles/temp", install=True)
# esg = Esgpull(path="/home/dchandan/scratch/blah")
files = esg.context.files(query)

for file in files:
    if file.filename == missing_file:
        print(file.url)
