import os

dir = "/data/Datasets/CMIP6/CMIP/NCC/NorCPM1/historical"
var = "pr"

for root, dirs, files in os.walk(dir):
    if files:
        if f"/{var}/" in root:
            # print(files)
            for filename in files:
                datestart = filename.strip().split("_")[-1]
                if datestart.startswith("2015") or datestart.startswith("2019"):
                    print(filename)
                    os.remove(os.path.join(root, filename))
