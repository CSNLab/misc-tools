# Miscellaneous Tools
This repository contains some miscellaneous utility snippets that may make your life easier.

See the docstring at the beginning of each file for detailed description, usage, examples, etc.

## Contents
#### `data_conversion_util.py`
A few functions to convert data files between json, csv and python dictionary/list, or wide and long format.

#### `randomization.py`
A script that randomize stimuli in a weird way (see the docstring in the file).

#### `trigger_sender.py`
Automatically send triggers by generating keyboard presses (so you can test an fMRI task script without an MRI scanner).

#### `organize_as_BIDS.py`
Rename and reorganize the fMRI data into the [Brain Imaging Data Structure (BIDS)](https://www.nature.com/articles/sdata201644).

---
### Neuroimaging Data Snippets:

#### `unsteady_volumns.py`
Detect the initial unsteady volumns in confounds.tsv, and remove those initial volumns from preproc files. Also check for big head movements and print the info. Run this script before `post_fmriprep_lv1.py`.

#### `post_fmriprep_lv1.py`
An example for level 1 analysis given data preprocessed by FMRIPREP. This script was adapted from [this notebook](https://github.com/poldrack/fmri-analysis-vm/blob/master/analysis/postFMRIPREPmodelling/First%20and%20Second%20Level%20Modeling%20(FSL).ipynb). Run this script after `unsteady_volumns.py`.

#### `create_masks.sh`
Create ROI masks in native space, given images parcellated by FreeSurfer recon-all.
