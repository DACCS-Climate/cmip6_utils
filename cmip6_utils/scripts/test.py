import os


for root, dirs, files in os.walk("CMIP"):
    # if files:  # we have reached the bottom level
    #     if f"/tas/" in root:
    #         # err = check_periods(files, root)
    #         # errcode = err[0]
    #         print(root)
    
    if root.endswith("tas"):
        print(os.listdir(root))
