#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
This script was adapted from
https://github.com/poldrack/fmri-analysis-vm/blob/master/analysis/postFMRIPREPmodelling/First%20and%20Second%20Level%20Modeling%20(FSL).ipynb
"""

import nipype.algorithms.modelgen as model   # model generation
from nipype.interfaces import fsl
from nipype.interfaces.base import Bunch
from nipype.caching import Memory
from bids.grabbids import BIDSLayout
import pandas as pd
import os


# Path
BIDS_DIR = '/u/project/cparkins/data/hierarchy/'
PREPROC_DIR = '/u/project/cparkins/data/hierarchy/fmriprep/output/fmriprep/'
MEM_DIR = '/u/flashscratch/m/mengdu/nav/'
# Subjects & runs
SUBJECTS = ['145', '146', '148']
EXCLUDING = {4: 5}  # excluding the 6th run from the 5th subject in the above list
# Experiment info
task = 'face'
num_runs = 6
conditions = ['u', 'd']
onsets = lambda event: [list(event[event.direction == 'u'].onset),
                            list(event[event.direction == 'd'].onset)]
durations = lambda event: [list(event[event.direction == 'u'].duration - 2),
                           list(event[event.direction == 'd'].duration - 2)]
# Conditions
up_cond = ['u', 'T', ['u'], [1]]
down_cond = ['d', 'T', ['d'], [1]]
all_nav = ['All nav', 'F', [up_cond, down_cond]]
contrasts = [up_cond, down_cond, all_nav]


def get_events(func_files):
    events = []
    for s in range(len(SUBJECTS)):
        events.append([])
        for r in range(num_runs):
            subj = func_files[s][r].subject
            run = func_files[s][r].run
            filename = 'sub-%s/func/sub-%s_task-%s_run-%s_events.tsv' % (subj, subj, task, run.zfill(2))
            events[s].append(pd.read_csv(os.path.join(BIDS_DIR, filename), sep="\t"))
    return events


def get_confounds(func_files):
    confounds = []
    for s in range(len(SUBJECTS)):
        confounds.append([])
        for r in range(num_runs):
            func_file = func_files[s][r]
            tsvname = 'sub-%s_task-%s_run-%s_bold_confounds.tsv' % (func_file.subject, task, func_file.run.zfill(2))
            confounds[s].append(pd.read_csv(os.path.join(PREPROC_DIR,
                                                         'sub-%s' % func_file.subject,
                                                         'func',
                                                         tsvname),
                                            sep="\t", na_values='n/a'))
    return confounds


def get_info(events, confounds):
    info = []
    for s in range(len(SUBJECTS)):
        info.append([])
        for r in range(num_runs):
            event = events[s][r]
            info[s].append([Bunch(conditions=conditions,
                                  onsets=onsets(event),
                                  durations=durations(event),
                                  regressors=[list(confounds[s][r].FramewiseDisplacement.fillna(0)),
                                              list(confounds[s][r].aCompCor00),
                                              list(confounds[s][r].aCompCor01),
                                              list(confounds[s][r].aCompCor02),
                                              list(confounds[s][r].aCompCor03),
                                              list(confounds[s][r].aCompCor04),
                                              list(confounds[s][r].aCompCor05),
                                              list(confounds[s][r].X),
                                              list(confounds[s][r].Y),
                                              list(confounds[s][r].Z),
                                              list(confounds[s][r].RotX),
                                              list(confounds[s][r].RotY),
                                              list(confounds[s][r].RotZ)],
                                  regressor_names=['FramewiseDisplacement',
                                                   'aCompCor00',
                                                   'aCompCor01',
                                                   'aCompCor02',
                                                   'aCompCor03',
                                                   'aCompCor04',
                                                   'aCompCor05',
                                                   'X',
                                                   'Y',
                                                   'Z',
                                                   'RotX',
                                                   'RotY',
                                                   'RotZ'])])
    return info


def specify_model(layout, func_files, info):
    specify_model_results = []
    for s in range(len(SUBJECTS)):
        specify_model_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            func_file = func_files[s][r]
            spec = model.SpecifyModel()
            spec.inputs.input_units = 'secs'
            spec.inputs.functional_runs = [os.path.join(
                PREPROC_DIR,
                'sub-%s' % func_file.subject,
                'func',
                'sub-%s_task-%s_run-%s_bold_space-T1w_preproc.nii.gz' % (func_file.subject, task, func_file.run.zfill(2))
            )]
            spec.inputs.time_repetition = layout.get_metadata(func_files[s][r].filename)['RepetitionTime']
            spec.inputs.high_pass_filter_cutoff = 128.
            spec.inputs.subject_info = info[s][r]
            specify_model_results[s].append(spec.run())
    return specify_model_results


def lv1_design(mem, layout, func_files, specify_model_results):
    level1design = mem.cache(fsl.model.Level1Design)
    level1design_results = []
    for s in range(len(SUBJECTS)):
        level1design_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            tr = layout.get_metadata(func_files[s][r].filename)['RepetitionTime']
            level1design_results[s].append(level1design(
                interscan_interval=tr,
                bases={'dgamma': {'derivs': True}},
                session_info=specify_model_results[s][r].outputs.session_info,
                model_serial_correlations=True,
                contrasts=contrasts
            ))
    return level1design_results


def feat_model(mem, level1design_results):
    modelgen = mem.cache(fsl.model.FEATModel)
    modelgen_results = []
    for s in range(len(SUBJECTS)):
        modelgen_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            modelgen_results[s].append(
                modelgen(fsf_file=level1design_results[s][r].outputs.fsf_files,
                         ev_files=level1design_results[s][r].outputs.ev_files))
    return modelgen_results


def masking(mem, func_files):
    mask = mem.cache(fsl.maths.ApplyMask)
    mask_results = []
    for s in range(len(SUBJECTS)):
        mask_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            subj = func_files[s][r].subject
            run = func_files[s][r].run
            preproc_name = 'sub-%s_task-%s_run-%s_bold_space-T1w_preproc.nii.gz' % (subj, task, run.zfill(2))
            mask_name = 'sub-%s_task-%s_run-%s_bold_space-T1w_brainmask.nii.gz' % (subj, task, run.zfill(2))
            mask_results[s].append(
                mask(in_file=os.path.join(PREPROC_DIR,
                                          'sub-%s' % subj,
                                          'func',
                                          preproc_name),
                     mask_file=os.path.join(PREPROC_DIR,
                                            'sub-%s' % subj,
                                            'func',
                                            mask_name)))
    return mask_results


def film_gls(mem, mask_results, modelgen_results):
    filmgls = mem.cache(fsl.FILMGLS)
    filmgls_results = []
    for s in range(len(SUBJECTS)):
        filmgls_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            filmgls_results[s].append(filmgls(in_file=mask_results[s][r].outputs.out_file,
                                              design_file=modelgen_results[s][r].outputs.design_file,
                                              tcon_file=modelgen_results[s][r].outputs.con_file,
                                              fcon_file=modelgen_results[s][r].outputs.fcon_file,
                                              autocorr_noestimate=True))
    return filmgls_results


def main():
    mem = Memory(base_dir=MEM_DIR)
    layout = BIDSLayout(BIDS_DIR)
    # func_files[subject_index][run_index]
    if num_runs > 1:
        func_files = [[layout.get(type='bold', task=task, run=i+1, subject=subj, extensions='nii.gz')[0]
                       for i in range(num_runs)] for subj in SUBJECTS]
    else:
        func_files = [layout.get(type='bold', task=task, subject=subj, extensions='nii.gz') for subj in SUBJECTS]
    events = get_events(func_files)
    confounds = get_confounds(func_files)
    info = get_info(events, confounds)
    specify_model_results = specify_model(layout, func_files, info)
    level1design_results = lv1_design(mem, layout, func_files, specify_model_results)
    modelgen_results = feat_model(mem, level1design_results)
    mask_results = masking(mem, func_files)
    film_gls(mem, mask_results, modelgen_results)


if __name__ == '__main__':
    main()
