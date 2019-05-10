#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
This script was adapted from
https://github.com/poldrack/fmri-analysis-vm/blob/master/analysis/postFMRIPREPmodelling/First%20and%20Second%20Level%20Modeling%20(FSL).ipynb

This script also handles the initial unsteady volumns of functional runs
(note: run unsteady_volumns.py to remove those volumns from preprocessed
files, before running this script).
Change line #25 - 45 as necessary, and double check line #90 - 94 to make
sure the confound regressors matches your need.
"""

import nipype.algorithms.modelgen as model   # model generation
from nipype.interfaces import fsl
from nipype.interfaces.base import Bunch
from nipype.caching import Memory
try:
    from bids.layout import BIDSLayout
except ModuleNotFoundError:
    from bids.grabbids import BIDSLayout
import pandas as pd
import os


# Paths
BIDS_DIR = '/u/project/cparkins/data/hierarchy/'
PREPROC_DIR = '/u/project/cparkins/data/hierarchy/fmriprep/output/fmriprep/'
MEM_DIR = '/u/project/cparkins/data/hierarchy/derivatives/lv1/work/'
# Subjects & runs
SUBJECTS = sorted([f[4:7] for f in os.listdir(PREPROC_DIR)
                   if f.startswith('sub') and f.endswith('.html')])  # find all html file names
EXCLUDING = {}  # e.g. {4: 5} excludes the 6th run from the 5th subject (0-indexed) in the SUBJECTS list
# Experiment info
task = 'face'
num_runs = 6
conditions = ['u', 'd']
onsets = lambda event, remove: [list(event[event.direction == 'u'].onset - remove),
                                list(event[event.direction == 'd'].onset - remove)]
durations = lambda event, remove: [list(event[event.direction == 'u'].duration - remove),
                                   list(event[event.direction == 'd'].duration - remove)]
# Conditions
tstats = [[cond, 'T', [cond], [1]] for cond in conditions]
fstat = ['all', 'F', tstats]
contrasts = tstats + [fstat]


def get_events(func_files):
    events = []
    for s in range(len(SUBJECTS)):
        events.append([])
        for r in range(num_runs):
            subj = func_files[s][r].subject
            if num_runs == 1:
                filename = 'sub-%s/func/sub-%s_task-%s_events.tsv' % (subj, subj, task)
            else:
                run = func_files[s][r].run
                filename = 'sub-%s/func/sub-%s_task-%s_run-%s_events.tsv' % (subj, subj, task, str(run).zfill(2))
            events[s].append(pd.read_csv(os.path.join(BIDS_DIR, filename), sep="\t"))
    return events


def get_confounds(func_files):
    confounds = []
    for s in range(len(SUBJECTS)):
        confounds.append([])
        for r in range(num_runs):
            func_file = func_files[s][r]
            if num_runs == 1:
                tsvname = 'sub-%s_task-%s_bold_confounds.tsv' % (func_file.subject, task)
            else:
                tsvname = 'sub-%s_task-%s_run-%s_bold_confounds.tsv' % (func_file.subject, task, str(func_file.run).zfill(2))
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
            df = confounds[s][r]
            # find how many rows to remove
            cols = [c for c in df.columns if c.startswith('NonSteadyStateOutlier')]
            unsteady = df[cols].sum(axis=1)
            remove_until = len(unsteady[unsteady == 1].index)
            # find names of confounds
            regressor_names = [c for c in df.columns if (c.startswith('aCompCor')
                               or c.startswith('Cosine') or c.startswith('AROMAAggrComp'))]
            regressor_names += ['CSF', 'WhiteMatter', 'GlobalSignal', 'X', 'Y', 'Z',
                                'RotX', 'RotY', 'RotZ']
            regressors = [list(confounds[s][r][conf][remove_until:]) for conf in regressor_names]
            # print(SUBJECTS[s], r, remove_until, regressor_names)
            
            run_onsets = onsets(event, remove=remove_until)
            run_durations = durations(event, remove=0)

            # if onset < 0 due to NonSteadyState removal, change it to 0 and reduce the duration too
            for i in range(len(run_onsets)):
                for j in range(len(run_onsets[i])):
                    if run_onsets[i][j] < 0:
                        run_durations[i][j] += run_onsets[i][j]
                        run_durations[i][j] = max(0, run_durations[i][j])
                        run_onsets[i][j] = 0

            event = events[s][r]
            info[s].append([Bunch(conditions=conditions,
                                  onsets=run_onsets,
                                  durations=run_durations,
                                  regressors=regressors,
                                  regressor_names=regressor_names)])
    return info


def specify_model(layout, func_files, info):
    specify_model_results = []
    for s in range(len(SUBJECTS)):
        specify_model_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            func_file = func_files[s][r]
            if num_runs == 1:
                filename = 'sub-%s_task-%s_bold_space-T1w_preproc.nii.gz' % (func_file.subject, task)
            else:
                filename = 'sub-%s_task-%s_run-%s_bold_space-T1w_preproc.nii.gz' % (func_file.subject, task, str(func_file.run).zfill(2))
            spec = model.SpecifyModel()
            spec.inputs.input_units = 'secs'
            spec.inputs.functional_runs = [os.path.join(
                PREPROC_DIR,
                'sub-%s' % func_file.subject,
                'func',
                filename
            )]
            spec.inputs.time_repetition = layout.get_metadata(func_files[s][r].path)['RepetitionTime']
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
            tr = layout.get_metadata(func_files[s][r].path)['RepetitionTime']
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
            if num_runs == 1:
                preproc_name = 'sub-%s_task-%s_bold_space-T1w_preproc.nii.gz' % (subj, task)
                mask_name = 'sub-%s_task-%s_bold_space-T1w_brainmask.nii.gz' % (subj, task)
            else:
                run = func_files[s][r].run
                preproc_name = 'sub-%s_task-%s_run-%s_bold_space-T1w_preproc.nii.gz' % (subj, task, str(run).zfill(2))
                mask_name = 'sub-%s_task-%s_run-%s_bold_space-T1w_brainmask.nii.gz' % (subj, task, str(run).zfill(2))
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
    print('Running subjects:', str(SUBJECTS))
    if not os.path.isdir(MEM_DIR):
        os.mkdir(MEM_DIR)
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
