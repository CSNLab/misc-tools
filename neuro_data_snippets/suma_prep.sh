#!/bin/bash

# This snippet prepares suma files that can be later used to create ROI
# masks (see create_masks.py)

# step1() converts freesurfer files to suma files (i.e., make ASCII
# versions of left and right hemisphere), and move them to a scratch
# directory

# step2() helps check the alignment of the suma files -- you still
# have to check them manually, but this function helps you open files
# with afni and suma so you don't need to type the same stuff for every
# subject.
# When running step2, afni and suma will open up -- press 't' in the suma
# window to see the files show up in afni so you can check if they look
# right. When you are done, close both programs and then press any key in
# the terminal to open them again for the next subject.


. /u/local/Modules/default/init/modules.sh
module load afni
module load freesurfer/6.0.0


# path to the freesurfer files output by fmriprep
fsPath="/u/project/CCN/cparkins/data/hierarchy/fmriprep/r1_output/freesurfer"
# path to a scratch directory -- suma output will be moved there after step 1 (because they are large)
workingPath="$SCRATCH/suma"
# a list of subjects to process
subjectList=(sub-132 sub-133 sub-134 sub-136 sub-137 sub-138 sub-139 sub-142 sub-143 sub-144)


function step1() {
    # convert freesurfer files to suma files
    for sid in "${subjectList[@]}"  # loop though subjects
    do
        cd $fsPath/$sid
        echo "converting $sid"
        @SUMA_Make_Spec_FS -NIFTI -sid $sid
        # move output to $workingPath
        mv SUMA $workingPath/$sid
    done
}

function step2() {
    # check alignment
    for sid in "${subjectList[@]}"
    do
        cd $workingPath/$sid
        echo "checking $sid"
        afni -niml &
        suma -spec $sid\_both.spec -sv $sid\_SurfVol.nii &
        # Press 't' in suma to show alignment in afni.
        # Close the current afni and suma windows when done,
        # then press any key in the terminal to continue to the next subject.
        read -n 1 -s
    done
}

step1
# step2



# step3 is now unnecessary after adding the -NIFTI flag in step 1
# function step3() {
#     bidsPath="/u/project/CCN/cparkins/data/hierarchy"
#     outPath="/u/project/CCN/cparkins/data/hierarchy/derivatives/aseg_aparc"
#     # align stuff with experiment anatomy
#     for sid in "${subjectList[@]}"
#     do
#         cd $outPath
#         mkdir $sid
#         cd $sid
#         ln -s $bidsPath/$sid/anat/$sid\_T1w.nii.gz $sid\_T1w.nii.gz
#         subSumaPath=$workingPath/$sid
#         @SUMA_AlignToExperiment -exp_anat $sid\_T1w+orig                    \
#                                 -surf_anat $subSumaPath/$sid\_SurfVol.nii   \
#                                 -atlas_followers                            \
#                                 -align_centers
#         3dAllineate -master $bidsPath/$sid/anat/$sid\_T1w.nii.gz    \
#                     -1Dmatrix_apply $sid\_SurfVol\_Alnd\_Exp.A2E.1D \
#                     -input $subSumaPath/aseg.nii                    \
#                     -prefix $sid\_aseg_Alnd_Exp+orig                \
#                     -final NN
#     done
# }
