#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
This script creates ROI masks in the native space, given input files prepared
by suma (see suma_prep.sh). You may need to change all of the paths and parameters
from line #17 to #36.
"""


from __future__ import print_function
import os
import re
import subprocess


# path and file name of the lookup table output by suma
lt_path = '/u/flashscratch/m/mengdu/suma'  
lt_file = 'aparc+aseg_rank.niml.lt'
# a regular expression to be used to find the ROI
# change line #55 (output mask name) together with this line!!!
roi_regex = r'"\d+" "ctx-[lr]h-superiorparietal"'
# 2 matches ('lh', 'rh') of the above regex are supposed to be found for each subject
num_matches = 2
# path and file name of the parcellation file output by suma
# (this file should be in alignment with t1w and functional file)
alnd_aparc_path = '/u/flashscratch/m/mengdu/suma'
alnd_aparc_file = 'aparc+aseg_rank.nii'
# a functional file to be used for resampling (any functional file is fine)
func_file = '/u/project/cparkins/data/hierarchy/derivatives/lv1/tstats/sac_tstats/sub-%s_sac.nii.gz'
# dilation radius in mm
dilation_radius = 7.2
# all .nii files will be moved to this path at the end of this script
output_path = 'spl_masks'
# a list of subjects to process
subject_list = ['132', '133', '134', '136', '137', '138', '139', '142', '143', '144']


def sh(cmd):  # run shell commands
    print(cmd + '\n')
    subprocess.call(cmd, shell=True)


sh('. /u/local/Modules/default/init/modules.sh; module use /u/project/CCN/apps/modulefiles; module load fsl/5.0.10')

for sid in subject_list:
    print('Processing subject %s...\n' % sid)
    # find the number cooresponding to the ROI
    with open(lt_path + '/sub-' + sid + '/' + lt_file, 'r') as lt:
        content = lt.read()
    lines = re.findall(roi_regex, content)
    if len(lines) != num_matches:
        print('ERROR: Found %d match(es) of the regular expression for subject %s.' % (len(lines), sid))
        continue
    for line in lines:
        splited = line.split('" "')  # splited[0] is the brain region id; splited[1] is its name
        index = splited[0][1:]  # splited[0][0] and splited[1][-1] are quotes
        region = splited[1][4] + 'h_spl'  # output mask name; change this line together with line #22
        # creating a mask with fsl
        roi_filename = 'sub-%s_%s' % (sid, region)
        aparc_file = alnd_aparc_path + '/sub-' + sid + '/' + alnd_aparc_file
        # get the roi
        cmd = 'fslmaths %s -thr %s -uthr %s -bin %s' % (aparc_file, index, index, roi_filename)
        sh(cmd)
        # resample the above mask so it has the same resolution as the functional files
        cmd = 'flirt -in %s.nii.gz -ref %s -applyxfm -usesqform -out %s_rsmp.nii.gz' % \
              (roi_filename, func_file % sid, roi_filename)
        sh(cmd)
        cmd = 'fslmaths %s_rsmp.nii.gz -thr 0.5 -bin %s_rsmp.nii.gz' % (roi_filename, roi_filename)
        sh(cmd)
        # dilate the mask
        cmd = 'fslmaths %s_rsmp.nii.gz -kernel sphere %f -dilF %s_rsmp_dil.nii.gz' % \
              (roi_filename, dilation_radius, roi_filename)
        sh(cmd)
    # move .nii files to output_path
    cmd = 'mv *.nii.gz %s/' % output_path
    sh(cmd)
