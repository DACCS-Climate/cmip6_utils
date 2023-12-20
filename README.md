The package consists of the `cmip6_utils` module and various command line scripts.

## Command line scripts



### cmip6_count_files
This program counts the number of datasets and individual files found for the given CMIP6 variable and experiment.

### cmip6_download_unsuccessful_files
This program loops over the files that were not successfully downloaded by `esgpull` and attempts to download them.

### cmip6_check_consistency
Checks the consistency of a dataset, i.e. check if all the data files are present.

### cmip6_download_file
Attempts to download a specific data file.

### find_download_missing_files
This scripts attempts to find all missing files for a dataset and download it. It assumes that the files in the dataset
are 1 year in length.

### cmip6_download_dataset
This script is similar to `find_download_missing_files` but makes no assumptions about the structure of dataset files. 
It goes and searches all files it can find for the dataset and downloads them. 

### cmip6_combine
Combines individual files into a single dataset file.

### cmip6_empty_dirs
> [!NOTE]
> This script is a work in progress.

This script lists the dataset directories that do not have any files in them.

### fix1849issueECEarth3
This script fixes an issue in some EC Earth data files where the data files start with data from Dec 1849.

### fix_NorCPM_date_issue
This script fixes an issue with files with odd end dates in NorCPM model outputs.

### cmip6_confirm_single_files
Checks that all datasets have single files. This usually is only the case after `cmip6_combine`.

### cmip6_find_duplicate_versions
Checks to see which datasets have duplicate versions of data. It can also remove duplicate versions if asked.

### cmip6_move_to_thredds
This is the last script one will need to use in their workflow. It moves combined data files from the staging directory 
to a directory on the THREDDS server.
