"""
Detect the initial unsteady volumns in confounds.tsv, and
remove those initial volumns from preproc files.
Also check for big movements and print the info.

The original preproc file will be renamed as "unsteady_" +
original name, and the processed file will be named same as
the original preproc file name.
If no unsteady state is present in confounds.tsv, the file
remains unchanged.

Load fsl/5.0.10 before running this.
"""

import os
import pandas as pd
import subprocess

PATH = '../fmriprep/'
SUBJECTS = ['sub-132', 'sub-133', 'sub-134', 'sub-136', 'sub-137', 'sub-138', 'sub-139', 'sub-142', 'sub-143', 'sub-144', 'sub-145', 'sub-146', 'sub-148', 'sub-149', 'sub-154', 'sub-155', 'sub-156', 'sub-157', 'sub-159', 'sub-160', 'sub-161', 'sub-163', 'sub-166', 'sub-167', 'sub-169', 'sub-170', 'sub-171', 'sub-172', 'sub-174', 'sub-175']
PREPROC_POSTFIX = 'space-T1w_preproc.nii.gz'  # things after "bold_"
XYZ_MOVEMENT_CRITERION = 2.5  # too big if larger than this; will just print the info and nothing else

all_rows = set()
for subj in SUBJECTS:
    filepath = PATH + subj + '/func/'
    filenames = [f for f in os.listdir(filepath)
                 if f.startswith('sub') and f.endswith('confounds.tsv')]
    for fname in sorted(filenames):
        df = pd.read_csv(filepath + fname, sep='\t')
        # look at XYZ axis movement
        for axis in ('X', 'Y', 'Z'):
            big_move = list(df[axis][df[axis] > XYZ_MOVEMENT_CRITERION])
            if len(big_move) > 0:
                print('Big movements in %s, %s axis:' % (fname, axis), big_move)
        # find unsteady rows
        cols = [c for c in df.columns if c.startswith('NonSteadyStateOutlier')]
        unsteady = df[cols].sum(axis=1)
        unsteady_rows = list(unsteady[unsteady == 1].index)
        num_unsteady = len(unsteady_rows)
        all_rows.update(unsteady_rows)
        print(fname + '\trows=' + str(unsteady_rows))
        if num_unsteady == 0:
            continue

        # remove first columns from preproc file
        preproc_name = fname[:fname.index('confounds.tsv')] + PREPROC_POSTFIX
        unsteady_name = 'unsteady_' + preproc_name
        print('Removing first %d volumns from ' % num_unsteady + preproc_name)
        os.rename(filepath + preproc_name, filepath + unsteady_name)
        subprocess.call('cd %s; fslroi %s %s %d -1' % (filepath, unsteady_name, preproc_name, num_unsteady), shell=True)

print('all unsteady rows:', all_rows)
