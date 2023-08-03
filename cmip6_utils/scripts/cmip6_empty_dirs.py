import os
from pathlib import Path

from cmip6_utils.dir import CMIPDirLevels, get_cmip_directories_at_level

for root, dirs, files in get_cmip_directories_at_level("/data/Datasets/CMIP6/CMIP", CMIPDirLevels.grid):
    for dir in dirs:
        dir = os.path.join(root, dir)
        if len(os.listdir(dir)) == 0:
            print(dir)
