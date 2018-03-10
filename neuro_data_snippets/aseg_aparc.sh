#!/bin/bash
. /u/local/Modules/default/init/modules.sh
module load afni
module load freesurfer/6.0.0

fsPath="/u/project/CCN/cparkins/data/hierarchy/fmriprep/r1_output/freesurfer"
workingPath="$SCRATCH/suma"
bidsPath="/u/project/CCN/cparkins/data/hierarchy"
outPath="/u/project/CCN/cparkins/data/hierarchy/derivatives/aseg_aparc"
subjectList=(sub-132 sub-133 sub-134 sub-136 sub-137 sub-138 sub-139 sub-142 sub-143 sub-144)

function step1() {
    # convert freesurfer files to suma files
    for sid in "${subjectList[@]}"  # loop though subjects
    do
        cd $fsPath/$sid
        echo "converting $sid"
        @SUMA_Make_Spec_FS -NIFTI -sid $sid
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

# step3 is now unnecessary after adding the -NIFTI flag in step 1
# function step3() {
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

step1
# step2
