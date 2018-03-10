#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import print_function
import os
import re
import subprocess


# path and file name of the lookup table output by suma
lt_path = '/u/flashscratch/m/mengdu/suma'  
lt_file = 'aparc+aseg_rank.niml.lt'
# a regular expression to be used to find the ROI
# change line #48 (output mask name) together with this line!!!
roi_regex = r'"\d+" "ctx-[lr]h-superiorparietal"'
# 2 matches ('lh', 'rh') of the above regex is supposed to be found for each subject
num_matches = 2
# path and file name of the parcellation file output by suma
# (this file should be in alignment with t1w and functional file)
alnd_aparc_path = '/u/flashscratch/m/mengdu/suma'
alnd_aparc_file = 'aparc+aseg_rank.nii'
# a functional file to be used for resampling (any functional file is fine)
func_file = '/u/project/CCN/cparkins/data/hierarchy/derivatives/aseg_aparc/orig_files_4_afni/sub-%s_sac+orig'
# all .nii files will be moved to this path at the end of this script
output_path = 'spl_masks'
# a list of subjects to process
subject_list = ['132', '133', '134', '136', '137', '138', '139', '142', '143', '144']


def sh(cmd):  # run shell commands
    print(cmd)
    subprocess.call(cmd, shell=True)


sh('module load afni')

for sid in subject_list:
    # find the number cooresponding to the ROI
    with open(lt_path + '/sub-' + sid + '/' + lt_file, 'r') as lt:
        content = lt.read()
    lines = re.findall(roi_regex, content)
    if len(lines) != num_matches:
        print('ERROR: Found %d match(es) of the regular expression for subject %s.' % (len(lines), sid))
        continue
    for line in lines:
        splited = line.split('" "')
        index = splited[0][1:]
        region = splited[1][4] + 'h_spl'  # output mask name; change this line together with line #15
        # afni commands below
        roi_filename = 'sub-%s_%s' % (sid, region)
        filepath = alnd_aparc_path + '/sub-' + sid + '/' + alnd_aparc_file
        # get a mask 
        cmd = "3dcalc -a %s'<%s>' " % (filepath, index) + \
                     "-prefix %s " % roi_filename + \
                     "-expr 'step(a)'"
        sh(cmd)
        # resample the above mask so it has the same resolution as the functional files
        cmd = '3dresample -master ' + func_file % sid + ' ' + \
                         '-rmode NN ' + \
                         '-input %s+orig. ' % roi_filename + \
                         '-prefix %s_resamp' % roi_filename
        sh(cmd)
        # convert the resampled mask to nifti
        cmd = '3dAFNItoNIFTI %s_resamp+orig. ' % roi_filename + \
                            '-prefix %s' % roi_filename
        sh(cmd)
    # move .nii files to output_path
    cmd = 'mv *.nii %s/' % output_path
    sh(cmd)
