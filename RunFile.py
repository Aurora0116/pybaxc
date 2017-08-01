##!/usr/bin/env python3
## -*- coding: utf-8 -*-
#"""
#Created on Fri Jul 28 10:44:38 2017
#
#@author: aki.nikolaidis
#"""
#
#import BASC
#from BASC import *
import numpy as np
from os.path import expanduser
from basc_workflow_runner import run_basc_workflow
import utils
import os

home = expanduser("~")
proc_mem= [2,4]




subject_file_list= [home + '/git_repo/BASC/sample_data/sub1/Func_Quarter_Res.nii.gz',
                    home + '/git_repo/BASC/sample_data/sub2/Func_Quarter_Res.nii.gz',
                    home + '/git_repo/BASC/sample_data/sub3/Func_Quarter_Res.nii.gz',
                    home + '/git_repo/BASC/sample_data/sub1/Func_Quarter_Res.nii.gz',
                    home + '/git_repo/BASC/sample_data/sub2/Func_Quarter_Res.nii.gz',
                    home + '/git_repo/BASC/sample_data/sub1/Func_Quarter_Res.nii.gz',
                    home + '/git_repo/BASC/sample_data/sub2/Func_Quarter_Res.nii.gz']

#'/Users/aki.nikolaidis/git_repo/BASC/sample_data/sub1/Func_Quarter_Res.nii.gz'

roi_mask_file= home + '/git_repo/BASC/masks/LC_Quarter_Res.nii.gz'
dataset_bootstraps=50
timeseries_bootstraps=10
n_clusters_list=[2,3,4]
output_sizes=[5,10,15,20]
bootstrap_list=list(range(0,dataset_bootstraps))
cross_cluster=True
roi2_mask_file= home + '/git_repo/BASC/masks/RC_Quarter_Res.nii.gz'
affinity_threshold= [0.9] * len(subject_file_list)
ism_gsm_stability=[]
run=True

for n_clusters in n_clusters_list:
    for output_size in output_sizes:
        out_dir= home + '/BASC_outputs/multi_set/dim_' + str(output_size) + '_' + str(n_clusters) + '_clusters'
        basc_test= run_basc_workflow(subject_file_list, roi_mask_file, dataset_bootstraps, timeseries_bootstraps, n_clusters, output_size, bootstrap_list, proc_mem, cross_cluster=cross_cluster, roi2_mask_file=roi2_mask_file, affinity_threshold=affinity_threshold, out_dir=out_dir, run=run)
        ism_gsm_stability.append(np.load(out_dir + '/workflow_output/ism_gsm_corr_file/ism_gsm_corr.npy'))

    print('saving files: ism_gsm_stability')
    ism_gsm_stability_file=os.path.join(out_dir, 'ism_gsm_stability_'+ str(n_clusters)+ '.npy')
    np.save(ism_gsm_stability_file, ism_gsm_stability)
    ism_gsm_stability=[]