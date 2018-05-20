#!/usr/bin/env python

"""
This script moves and renames the necessary files (FILES_NEEDED) resulted
from Nipype post-fmriprep level 1 modeling, and merges multiple tstat files
for one subject into one file with fslmerge.

Load fsl/5.0.10 before running this.
"""

from __future__ import print_function
import os
import re
import subprocess


NIPYPE_DIR = 'work/face/nipype_mem/nipype-interfaces-fsl-model-FILMGLS/'
OUTPUT_DIR = 'tstats/face_tstats/'
OUTPUT_FILE = 'tstats/face_tstats/%s_nav.nii.gz'  # %s will be filled with subject ID
REGEX = r'sub-\d+_task-\w+_run-\d+_bold_space-T1w_preproc_masked.nii.gz'  # a pattern to find in command.txt
FILES_NEEDED = ['tstat%d.nii.gz' % i for i in range(10)]


def rename(nipype_dir, output_dir):
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    for folder in os.listdir(nipype_dir):
        # find name
        if os.path.exists(nipype_dir + folder + '/command.txt'):
            with open(nipype_dir + folder + '/command.txt', 'r') as cmdfile:
                cmd = cmdfile.readline()
            nifti_name = re.search(REGEX, cmd).group()
            # change the 4 lines below based on your regular expression
            subject = nifti_name[4:7]
            task = nifti_name[13:17]
            run = nifti_name[22:24]
            new_name_prefix = 'sub-%s_%s_run-%s_' % (subject, task, run)
        else:
            print('Error:' + nipype_dir + folder + ' doesn\'t have a command.txt')
            continue
        # rename
        for filename in os.listdir(nipype_dir + folder + '/results/'):
            if filename in FILES_NEEDED:
                old_name = nipype_dir + folder + '/results/' + filename
                new_name = output_dir + new_name_prefix + filename
                if os.path.exists(new_name):
                    print('Error: Skipping ' + old_name + ' because ' + new_name + ' already exists.')
                    continue
                os.rename(old_name, new_name)
                print('Renamed "%s" to "%s".' % (old_name, new_name))


def sh(cmd):  # run shell commands
    print(cmd + '\n')
    subprocess.call(cmd, shell=True)


def fslmerge(outdir, outfile):
    # get all tstats file names
    tstat_files = [outdir + f for f in os.listdir(outdir) if f.endswith('.nii.gz') and f[-13:-8] == 'tstat']
    # get all unique subjects
    subjects = set([re.search(r'sub-\d+', f).group() for f in tstat_files])
    for subj in subjects:
        # run the merge command for each subject
        sub_tstat_files = sorted([f for f in tstat_files if subj in f])
        if os.path.exists(outfile % subj):
            print('Error: ' + outfile % subj + ' already exists. Skipping fslmerge.')
        else:
            cmd = 'fslmerge -t ' + outfile % subj + ' ' + ' '.join(sub_tstat_files)
            sh(cmd)


if __name__ == '__main__':
    rename(NIPYPE_DIR, OUTPUT_DIR)
    fslmerge(OUTPUT_DIR, OUTPUT_FILE)
