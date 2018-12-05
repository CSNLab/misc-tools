#!/bin/bash

# This script shows an example for mask creation. It takes input from freesurfer recon-all
# results, and creates masks of cortical ribbons for functional runs in subject native space.

# Note: If you are creating masks for a particular ROI, use a parcellation file as the input
# (replacing $freesurferDir/$sid/mri/ribbon.mgz). FMRIPREP should output parcellation files
# in sub-X/anat directories (e.g. sub-X_task-Y_bold_space-T1w_label-aseg_roi.nii.gz).
# To find out what value corresponds to what ROI  in the parcellation file, a lookup table
# can be found at $FREESURFER_HOME/FreeSurferColorLUT.txt. The first column of that file
# indicates the numbers shown in the parcellation files. You will need to change step b in
# this file to extract the number you want.


. /u/local/Modules/default/init/modules.sh
module load fsl/5.0.10

refDir="/u/project/cparkins/data/hierarchy/derivatives/fmriprep/"
freesurferDir="/u/project/cparkins/data/hierarchy/derivatives/freesurfer/"
maskDir="/u/project/CCN/cparkins/data/hierarchy/derivatives/masks"
outDir="$maskDir/ribbon_masks"
subjectList=(sub-132 sub-145 sub-161)


for sid in "${subjectList[@]}"
do
	# a) convert freesurfer ribbon.mgz to nifti
	mri_convert $freesurferDir/$sid/mri/ribbon.mgz $outDir/$sid\_ribbon.nii.gz
	# b) make a ribbon mask by taking out 3 (Left-Cerebral-Cortex) and 42 (Right-Cerebral-Cortex)
	#  1) minus 22.5  2) take absolute value  3) mask out everything other than 19.5  4) convert to binary
	fslmaths $outDir/$sid\_ribbon.nii.gz -sub 22.5 -abs -thr 19.5 -uthr 19.5 -bin $outDir/$sid\_ribbon.nii.gz
	# c) resample
	flirt -in $outDir/$sid\_ribbon.nii.gz -ref $refDir/$sid/func/$sid\_task-face_run-01_bold_space-T1w_preproc.nii.gz -applyxfm -usesqform -out $outDir/$sid\_ribbon_rsmp.nii.gz
	fslmaths $outDir/$sid\_ribbon_rsmp.nii.gz -thr 0.5 -bin $outDir/$sid\_ribbon_rsmp.nii.gz
	# d) dilate
	fslmaths $outDir/$sid\_ribbon_rsmp.nii.gz -kernel sphere 7.2 -dilM $outDir/$sid\_ribbon_rsmp_dil.nii.gz
done
