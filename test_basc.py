import os
import time
from os.path import expanduser
import matplotlib
import numpy as np
import nibabel as nb
import pandas as pd
import nilearn.image as image
import scipy as sp


from nilearn import datasets
from nilearn.input_data import NiftiMasker
from nilearn.plotting import plot_roi, show
from nilearn.image.image import mean_img
from nilearn.image import resample_img
from matplotlib import pyplot as plt


from sklearn import cluster, datasets
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler
#

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util


matplotlib.style.use('ggplot')
home = expanduser("~")


def test_timeseries_bootstrap():
    """
    Tests the timeseries_bootstrap method of BASC workflow
    """
    np.random.seed(27)
    #np.set_printoptions(threshold=np.nan)
    
    # Create a 10x5 matrix which counts up by column-wise
    x = np.arange(50).reshape((5,10)).T
    actual = timeseries_bootstrap(x,3)
    desired = np.array([[ 4, 14, 24, 34, 44],
                       [ 5, 15, 25, 35, 45],
                       [ 6, 16, 26, 36, 46],
                       [ 8, 18, 28, 38, 48],
                       [ 9, 19, 29, 39, 49],
                       [ 0, 10, 20, 30, 40],
                       [ 7, 17, 27, 37, 47],
                       [ 8, 18, 28, 38, 48],
                       [ 9, 19, 29, 39, 49],
                       [ 8, 18, 28, 38, 48]])
    np.testing.assert_equal(actual, desired)


def test_standard_bootstrap():
    """
    Tests the standard_bootstrap method of BASC workflow
    """
    np.random.seed(27)
    x = np.arange(50).reshape((5,10)).T
    actual = standard_bootstrap(x)
    desired = np.array([[ 3, 13, 23, 33, 43],
                        [ 8, 18, 28, 38, 48],
                        [ 8, 18, 28, 38, 48],
                        [ 8, 18, 28, 38, 48],
                        [ 0, 10, 20, 30, 40],
                        [ 5, 15, 25, 35, 45],
                        [ 8, 18, 28, 38, 48],
                        [ 1, 11, 21, 31, 41],
                        [ 2, 12, 22, 32, 42],
                        [ 1, 11, 21, 31, 41]])
    np.testing.assert_equal(actual, desired)

def test_adjacency_matrix():
    """
    Tests the adjacency_matrix of BASC workflow
    """
    x = np.asarray([1, 2, 2, 3, 1])[:,np.newaxis]
    actual = adjacency_matrix(x).astype(int)
    desired = np.array([[1, 0, 0, 0, 1],
                       [0, 1, 1, 0, 0],
                       [0, 1, 1, 0, 0],
                       [0, 0, 0, 1, 0],
                       [1, 0, 0, 0, 1]])
    np.testing.assert_equal(actual, desired)

def generate_blobs():
    np.random.seed(27)
    offset = np.random.randn(30)

    x1 = np.random.randn(200,30) + 2*offset
    x2 = np.random.randn(100,30) + 44*np.random.randn(30)
    x3 = np.random.randn(400,30)
    blobs = np.vstack((x1,x2,x3))
    return blobs


def generate_simple_blobs(x):
    np.random.seed(x)
    offset = np.random.randn(30)

    x1 = np.random.randn(200,30) + 2*offset
    x2 = np.random.randn(100,30) + 44*np.random.randn(30)+ 2*offset

    blobs = np.vstack((x1,x2))
    return blobs



def generate_blobs_3d():
    np.random.seed(27)
    x1 = np.random.randn(200,3) + np.array([1.4, 1.8, 22.2])
    x2 = np.random.randn(100,3) + np.array([4.7, 4.0, 9.6])
    x3 = np.random.randn(400,3) + np.array([100.7, 100.0, 100.8])
    blobs = np.vstack((x1,x2,x3))
    return blobs

def test_cluster_timeseries():
    """
    Tests the cluster_timeseries method on three blobs in three dimensions (to make correlation possible)
    """
    blobs = generate_blobs_3d()
    y_predict = cluster_timeseries(blobs, 3, similarity_metric = 'correlation')


def test_cross_cluster_timeseries():
    np.random.seed(30)
    offset = np.random.randn(30)
    x1 = np.random.randn(20,30) + 10*offset
    x2 = np.random.randn(10,30) + 44*np.random.randn(30)
    sampledata1 = np.vstack((x1,x2))
    sampledata2 = sampledata1
    actual = cross_cluster_timeseries(sampledata1, sampledata2, 2, 'correlation')
    desired = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1,
       1, 1, 1, 1, 1, 1, 1])
    np.testing.assert_equal(actual,desired)


def test_individual_stability_matrix():
    """
    Tests individual_stability_matrix method on three gaussian blobs.
    """

    blobs = generate_blobs()
    ism = individual_stability_matrix(blobs, 10, 3)

    assert False

def test_cross_cluster_individual_stability_matrix():
    """
    Tests individual_stability_matrix method on three gaussian blobs.
    """

    blobs1 = generate_simple_blobs(27)
    blobs2 = generate_simple_blobs(27)
    blobs2 = blobs2[0:150,:]
    ism = individual_stability_matrix(blobs1, 10, 2, Y2 = blobs2, cross_cluster = True)

    return ism

def test_nifti_individual_stability():

    subject_file = '/Users/aki.nikolaidis/Desktop/NKI_SampleData/A00060280/reduced50.nii.gz'

    roi_mask_file=home + '/C-PAC/CPAC/basc/sampledata/masks/BG.nii.gz'
    roi2_mask_file=home + '/C-PAC/CPAC/basc/sampledata/masks/yeo_2.nii.gz'
    
   
    n_bootstraps=100
    n_clusters=2
    output_size=20
    cross_cluster=True
    
    cbb_block_size=None
    affinity_threshold=0.5
    nifti_individual_stability(subject_file, roi_mask_file, n_bootstraps, n_clusters, output_size, cross_cluster, roi2_mask_file, cbb_block_size, affinity_threshold)


def test_cluster_matrix_average():
    
    G, cluster_G, cluster_voxel_scores, gsm_file, clusters_G_file, cluster_voxel_scores_file = new_test_group_stability_matrix()
    ism = test_cross_cluster_individual_stability_matrix()
    cluster_voxel_scores=cluster_matrix_average(G, cluster_G)

def new_test_group_stability_matrix():
    """
    Tests group_stability_matrix method.  This creates a dataset of blobs varying only by additive zero-mean gaussian
    noise and calculates the group stability matrix.
    """
    import utils
    import basc
    
    bootstrap=20
    blobs = generate_blobs()

    ism_dataset = np.zeros((5, blobs.shape[0], blobs.shape[0]))
    ism_list = []
    for i in range(ism_dataset.shape[0]):
        ism_dataset[i] = utils.individual_stability_matrix(blobs + 0.2*np.random.randn(blobs.shape[0], blobs.shape[1]), 10, 3, affinity_threshold = 0.0)
        f = 'ism_dataset_%i.npy' % i
        ism_list.append(f)
        np.save(f, ism_dataset[i])

    indiv_stability_list=ism_list
    n_bootstraps=10
    n_clusters=3

    
    G = basc.map_group_stability(ism_list, 10, 3)
   # for boot in 
#    cluster_G, cluster_voxel_scores, gsm_file, clusters_G_file, cluster_voxel_scores_file
#    
#    def join_group_stability(group_stability_list, n_bootstraps, n_clusters):
#    
#    return G, cluster_G, cluster_voxel_scores, gsm_file, clusters_G_file, cluster_voxel_scores_file


def test_group_stability_matrix():
    """
    Tests group_stability_matrix method.  This creates a dataset of blobs varying only by additive zero-mean gaussian
    noise and calculates the group stability matrix.
    """
    blobs = generate_blobs()

    ism_dataset = np.zeros((5, blobs.shape[0], blobs.shape[0]))
    ism_list = []
    for i in range(ism_dataset.shape[0]):
        ism_dataset[i] = individual_stability_matrix(blobs + 0.2*np.random.randn(blobs.shape[0], blobs.shape[1]), 10, 3, affinity_threshold = 0.0)
        f = 'ism_dataset_%i.npy' % i
        ism_list.append(f)
        np.save(f, ism_dataset[i])

    G, cluster_G, cluster_voxel_scores = group_stability_matrix(ism_list, 10, 3, [0,1,1,1,0])

    return G, cluster_g, cluster_voxel_scores


def test_basc_workflow_runner():

    from basc_workflow_runner import run_basc_workflow
    import utils
    subject_file_list= [home + '/git_repo/BASC/sample_data/sub1/Func_Quarter_Res.nii.gz',
                        home + '/git_repo/BASC/sample_data/sub2/Func_Quarter_Res.nii.gz',
                        home + '/git_repo/BASC/sample_data/sub3/Func_Quarter_Res.nii.gz']

    roi_mask_file= home + '/git_repo/BASC/masks/LC_Quarter_Res.nii.gz'
    dataset_bootstraps=50
    timeseries_bootstraps=10
    n_clusters=4
    output_size=10
    bootstrap_list=list(range(0,dataset_bootstraps))
    cross_cluster=True
    roi2_mask_file= home + '/git_repo/BASC/masks/RC_Quarter_Res.nii.gz'
    affinity_threshold= [0.5, 0.5, 0.5]
    out_dir= home + '/BASC_outputs'
    run=True
    
    

    basc_test= run_basc_workflow(subject_file_list, roi_mask_file, dataset_bootstraps, timeseries_bootstraps, n_clusters, output_size, bootstrap_list, cross_cluster=cross_cluster, roi2_mask_file=roi2_mask_file, affinity_threshold=affinity_threshold, out_dir=out_dir, run=run)



def test_basc_workflow_runner():

    from basc_workflow_runner import run_basc_workflow
    import utils
    subject_file_list=    ['/Users/aki.nikolaidis/BGDev_SampleData/A00060280/reduced100.nii.gz',
                           '/Users/aki.nikolaidis/BGDev_SampleData/A00060280/reduced100.nii.gz',
                           '/Users/aki.nikolaidis/BGDev_SampleData/A00060280/reduced100.nii.gz',
                           '/Users/aki.nikolaidis/BGDev_SampleData/A00060384/reduced100.nii.gz',
                           '/Users/aki.nikolaidis/BGDev_SampleData/A00060384/reduced100.nii.gz',
                           '/Users/aki.nikolaidis/BGDev_SampleData/A00060384/reduced100.nii.gz']

    roi_mask_file=home + '/git_repo/basc/masks/BG.nii.gz'
    dataset_bootstraps=10
    timeseries_bootstraps=50
    n_clusters=4
    output_size=500
    bootstrap_list=list(range(0,dataset_bootstraps))
    cross_cluster=True
    roi2_mask_file=home + '/git_repo/basc/masks/yeo_2.nii.gz'
    affinity_threshold= [0.5] * len(subject_file_list)
    out_dir= home + '/BASC_outputs'
    run=True
    
    

    basc_test= run_basc_workflow(subject_file_list, roi_mask_file, dataset_bootstraps, timeseries_bootstraps, n_clusters, output_size, bootstrap_list, cross_cluster=cross_cluster, roi2_mask_file=roi2_mask_file, affinity_threshold=affinity_threshold, out_dir=out_dir, run=run)




def heavy_basc_workflow_test():

    from basc_workflow_runner import run_basc_workflow
    import utils

    subject_file_list=['/Users/aki.nikolaidis/BGDev_SampleData/A00060846/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/Users/aki.nikolaidis/BGDev_SampleData/A00060603/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/Users/aki.nikolaidis/BGDev_SampleData/A00060503/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/Users/aki.nikolaidis/BGDev_SampleData/A00060429/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/Users/aki.nikolaidis/BGDev_SampleData/A00060384/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/Users/aki.nikolaidis/BGDev_SampleData/A00060280/bandpassed_demeaned_filtered_antswarp.nii.gz']


    roi_mask_file=home + '/git_repo/basc/masks/BG.nii.gz'
   
    dataset_bootstraps=50
    timeseries_bootstraps=10
    n_clusters=2
    output_size=10
    cross_cluster=True
    
    roi2_mask_file=home + '/git_repo/basc/masks/yeo_2.nii.gz'
    
    affinity_threshold= [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    out_dir= home + '/BASC_outputs'
    run=True
    

    basc_test= run_basc_workflow(subject_file_list, roi_mask_file, dataset_bootstraps, timeseries_bootstraps, n_clusters, output_size, cross_cluster=cross_cluster, roi2_mask_file=roi2_mask_file, affinity_threshold=affinity_threshold, out_dir=out_dir, run=run)

def NED_heavy_basc_workflow_test():
#%%

    
    from basc_workflow_runner import run_basc_workflow
    import utils
    import time
    matrixtime = time.time()

#    subject_file_list= ['/data/rockland_sample/A00060603/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
#                         '/data/rockland_sample/A00060503/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
#                         '/data/rockland_sample/A00060429/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
#                         '/data/rockland_sample/A00060384/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
#                         '/data/rockland_sample/A00060280/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
#                         '/data/rockland_sample/A00059935/functional_mni/_scan_dsc_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
#                         '/data/rockland_sample/A00059875/functional_mni/_scan_dsc_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
#                         '/data/rockland_sample/A00059734/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
#                         '/data/rockland_sample/A00059733/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz']

    subject_file_list= ['/data/Projects/anikolai/rockland_downsampled/A00018030/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00027159/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00027167/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00027439/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00027443/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00030980/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00030981/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00031216/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00031219/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00031410/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00031411/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00031578/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00031881/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00032008/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00032817/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00033231/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00033714/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00034073/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00034074/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00034350/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00035291/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00035292/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00035364/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00035377/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00035869/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00035940/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00035941/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00035945/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00037125/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00037368/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00037458/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00037459/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00037483/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00038603/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00038706/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00039075/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00039159/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00039866/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00040342/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00040440/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00040556/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00040798/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00040800/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00040815/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00041503/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00043240/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00043282/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00043494/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00043740/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00043758/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00043788/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00044084/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00044171/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00050743/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00050847/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00051063/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00051603/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00051690/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00051691/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00051758/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00052069/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00052165/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00052183/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00052237/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00052461/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00052613/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00052614/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00053203/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00053320/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00053390/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00053490/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00053744/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00053873/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00054206/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00055693/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00056703/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00057405/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00057480/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00057725/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00057862/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00057863/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00057967/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058004/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058053/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058060/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058061/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058215/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058229/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058516/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058537/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058570/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058685/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00058951/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00059109/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00059325/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00059427/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00059733/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00059734/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00059865/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00059875/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00059935/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00060280/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00060384/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00060429/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00060503/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00060603/3mm_resampled.nii.gz',
    '/data/Projects/anikolai/rockland_downsampled/A00060846/3mm_resampled.nii.gz']

    roi_mask_file=home + '/git_repo/BASC/masks/cerebellum_3mm.nii.gz'
   
    dataset_bootstraps=50
    timeseries_bootstraps=50
    n_clusters=3
    output_size=400
    cross_cluster=True
    bootstrap_list=list(range(0,dataset_bootstraps))

    roi2_mask_file=home + '/git_repo/BASC/masks/yeo2_3mm.nii.gz'
    
    affinity_threshold= [0.5] * 107 #[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    out_dir=   '/data/Projects/anikolai/BASC_outputs/CouilleCerebellum'
    run=True
    

    basc_test= run_basc_workflow(subject_file_list, roi_mask_file, dataset_bootstraps, timeseries_bootstraps, n_clusters, output_size, bootstrap_list, cross_cluster=cross_cluster, roi2_mask_file=roi2_mask_file, affinity_threshold=affinity_threshold, out_dir=out_dir, run=run)

    print((time.time() - matrixtime))
#%%

def NKI_Ned_test():
    
    
    imports = ['import os',
           'import nibabel as nb',
           'import numpy as np',
           'import scipy as sp',
           'from nipype.utils.filemanip import filename_to_list, list_to_filename, split_filename',
           'from scipy.special import legendre'
           ]
    
    subject_file_list= ['/data/rockland_sample/A00060603/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/data/rockland_sample/A00060503/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/data/rockland_sample/A00060429/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/data/rockland_sample/A00060384/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/data/rockland_sample/A00060280/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/data/rockland_sample/A00059935/functional_mni/_scan_dsc_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/data/rockland_sample/A00059875/functional_mni/_scan_dsc_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/data/rockland_sample/A00059734/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/data/rockland_sample/A00059733/functional_mni/_scan_clg_2_rest_645/bandpassed_demeaned_filtered_antswarp.nii.gz']
    
    subject_file_list = ['/home/anikolai/NKI_SampleData/A00060280/reduced50.nii.gz',
                         '/home/anikolai/NKI_SampleData/A00060384/reduced50.nii.gz',
                         '/home/anikolai/NKI_SampleData/A00060429/reduced50.nii.gz',
                         '/home/anikolai/NKI_SampleData/A00060503/reduced50.nii.gz',
                         '/home/anikolai/NKI_SampleData/A00060603/reduced50.nii.gz',
                         ]
    
    subject_file_list = ['/home/anikolai/NKI_SampleData/A00060280/reduced50.nii.gz',
                         '/home/anikolai/NKI_SampleData/A00060384/reduced50.nii.gz',
                        ]

    
    #/Users/aki.nikolaidis/Desktop
    subject_file_list=['/Users/aki.nikolaidis/BGDev_SampleData/A00060846/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/Users/aki.nikolaidis/BGDev_SampleData/A00060603/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/Users/aki.nikolaidis/BGDev_SampleData/A00060503/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/Users/aki.nikolaidis/BGDev_SampleData/A00060429/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/Users/aki.nikolaidis/BGDev_SampleData/A00060384/bandpassed_demeaned_filtered_antswarp.nii.gz',
                         '/Users/aki.nikolaidis/BGDev_SampleData/A00060280/bandpassed_demeaned_filtered_antswarp.nii.gz']

    from basc_workflow_runner import run_basc_workflow
    import utils
    import pandas as pd

    
    subject_file_list = ['/Users/aki.nikolaidis/Desktop/NKI_SampleData/A00060280/reduced50.nii.gz',
                         '/Users/aki.nikolaidis/Desktop/NKI_SampleData/A00060384/reduced50.nii.gz',
                        ]

    roi_mask_file=home + '/C-PAC/CPAC/basc/sampledata/masks/BG.nii.gz'
    roi2_mask_file=home + '/C-PAC/CPAC/basc/sampledata/masks/yeo_2.nii.gz'
    output_size = 20


    dataset_bootstraps=10
    timeseries_bootstraps=10
    n_clusters=2
    cross_cluster=True
    affinity_threshold= [0.5, 0.5]# , 0.5, 0.5, 0.5]
    out_dir= home + '/BASC_outputs'
    run=True
    
    basc_test= run_basc_workflow(subject_file_list, roi_mask_file, dataset_bootstraps, timeseries_bootstraps, n_clusters, output_size, cross_cluster=cross_cluster, roi2_mask_file=roi2_mask_file, affinity_threshold=affinity_threshold, out_dir=out_dir, run=run)


def bruteforce_workflow_test():

   
    subject_file_list = [home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz',
                         home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz',
                         home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz',
                         home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz',
                         home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz',
                         home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz',
                         home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz',
                         home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz',
                         home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz',
                         home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz']
    subject_file_list = ['/home/anikolai/NKI_SampleData/A00060280/reduced50.nii.gz',
                         '/home/anikolai/NKI_SampleData/A00060384/reduced50.nii.gz',
                        ]
    
    import time
    import utils 
    
    subject_file_list = ['/Users/aki.nikolaidis/Desktop/NKI_SampleData/A00060280/reduced50.nii.gz',
                         '/Users/aki.nikolaidis/Desktop/NKI_SampleData/A00060384/reduced50.nii.gz',
                        ]
    
    roi_mask_file=home + '/C-PAC/CPAC/basc/sampledata/masks/BG.nii.gz'
    roi2_mask_file=home + '/C-PAC/CPAC/basc/sampledata/masks/yeo_2.nii.gz'
    output_size = 2000


    dataset_bootstraps=10
    timeseries_bootstraps=10
    n_clusters=2
    cross_cluster=True
    affinity_threshold= [0.5, 0.5]# , 0.5, 0.5, 0.5]
    out_dir= home + '/BASC_outputs'
    run=True
    
    sample_file = home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/fixedfunc_2thirds_res.nii.gz'
    filename = home + '/C-PAC/CPAC/basc/sampledata/Striatum_GroupLevel_MotorCluster.nii.gz'
    
    

    roi_mask_file= home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/Striatum_2thirdsRes.nii.gz'
    dataset_bootstraps=50
    timeseries_bootstraps=50
    n_clusters=4
    cross_cluster=True
    roi2_mask_file= home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Data/Yeo_LowRes/yeo_2_2thirdsRes_bin.nii.gz'
    output_size = 500

    ism_list = []
    ism_dataset = np.zeros((len(subject_file_list), output_size, output_size))

    cbb_block_size=None
    #affinity_threshold=0.5
    n_bootstraps=timeseries_bootstraps

    


    start = time.time()
    for i in range(len(subject_file_list)):
        data = nb.load(subject_file_list[int(i)]).get_data().astype('float32')
        
        
        roi_mask_file_nb = nb.load(roi_mask_file)
        roi2_mask_file_nb= nb.load(roi2_mask_file)

        roi_mask_nparray = nb.load(roi_mask_file).get_data().astype('float32').astype('bool')
        roi2_mask_nparray = nb.load(roi2_mask_file).get_data().astype('float32').astype('bool')


        roi1data = data[roi_mask_nparray]
        roi2data = data[roi2_mask_nparray]

        data_dict1 = utils.data_compression(roi1data.T, roi_mask_file_nb, roi_mask_nparray, output_size)
        Y1_compressed = data_dict1['data'].T
        Y1_labels = pd.DataFrame(data_dict1['labels'])
        
        index=pd.DataFrame(np.arange(1,Y1_labels.shape[0]+1))
        
        
        data_dict2 = utils.data_compression(roi2data.T, roi2_mask_file_nb, roi2_mask_nparray, output_size)
        Y2_compressed = data_dict2['data'].T
        Y2_labels = pd.DataFrame(data_dict2['labels'])
        #ward  = utils.data_compression(roi1data.T, roi_mask_file_nb, roi_mask_nparray, output_size)
        #def data_compression(fmri_masked, mask_img, mask_np, output_size):

        
        print ('(%i voxels, %i timepoints and %i bootstraps)' % (Y1_compressed.shape[0], Y1_compressed.shape[1], n_bootstraps))
        print ('(%i voxels, %i timepoints and z%i bootstraps)' % (Y2_compressed.shape[0], Y2_compressed.shape[1], n_bootstraps))

        
        ism_dataset[int(i)] = utils.individual_stability_matrix(Y1_compressed, n_bootstraps, n_clusters, Y2_compressed, cross_cluster, cbb_block_size, affinity_threshold)
#################################################################################
#################################################################################
#################################################################################
        voxel_num=roi1data.shape[0]
        ism=ism_dataset[int(i)]
        expand_ism(voxel_num,ism)
    

        import time
        import random
        import pandas as pd
        import numpy as np
        C_mike = np.zeros(b)
        C_mike=pd.DataFrame(C_mike)
        matrixtime = time.time()
        for row in range(0,ism.shape[0]):
             print ('row is ', row)
             for column in range(0, ism.shape[1]):
                
                rowmatch = np.array(Y1_labels==row)
                rowmatch = rowmatch*1
                
                colmatch = np.array(Y1_labels==column)
                colmatch = colmatch*1
                
                match_matrix=rowmatch*colmatch.T
                C_mike=C_mike+(match_matrix*ism[row,column])
        print((time.time() - matrixtime))

                
#                target_mat=target_mat+(match_matrix*source_mat[row,column])
#                
#                
#                C_mike[Y1_labels==row,Y1_labels==column] = ism[row,column] 
#        
#        int(np.array((Y1_labels==row)).T) * (int(np.array((Y1_labels==column)).T)).T
#        


#############################STACK OVERFLOW SCRIPT##################################################
###############################STACK OVERFLOW SCRIPT###################################################
##############################STACK OVERFLOW SCRIPT###################################################
##############################STACK OVERFLOW SCRIPT############################################        

###TEST EXAMPLE OF DECOMPRESS
        import time
        import random
        import pandas as pd
        import numpy as np
        vec1=[]
        for x in range (0, 13000):
            vec1.append(random.randint(0, 19))
            
        #vec1=pd.DataFrame(vec1)
        vec1=np.array(vec1)
        
        import time
        import random
        import pandas as pd
        import numpy as np
        
        n=5
        k=3
        i=0
        vec1=[]
        for x in range(0, n):
            vec1.append(random.randint(0, k-1))
            
        #vec1=pd.DataFrame(vec1)
        vec1=np.array(vec1)
        #vec=pd.DataFrame(np.arange(0,300))
        #vec2=pd.concat([vec,vec1], axis=1)
        #sizevec1=vec1.shape[0]
        sizevec1=len(vec1)
        matshape=(sizevec1,sizevec1)
        target_mat=np.zeros(matshape)
        #target_mat=pd.DataFrame(target_mat)
        
        temp=np.random.random((n,n))
        source_mat=temp*temp.T
        
        ###Slow Method###
        
        matrixtime = time.time()
        for row in range(0,target_mat.shape[0]):
            for column in range(0,target_mat.shape[1]):
                #print 'row is ', row
                #print 'column is', column
                target_mat.iloc[row,column] = source_mat.item(int(vec1.iloc[row]), int(vec1.iloc[column]))
        print((time.time() - matrixtime))
        target_mat_slow=target_mat
        
        ###FasterMethod###

        target_mat=np.zeros(matshape)
        #target_mat=pd.DataFrame(target_mat)
        
        matrixtime = time.time()
        for row in range(0,source_mat.shape[0]):
            print ('row is ', row)
            for column in range(0, source_mat.shape[1]):
                
                rowmatch = np.array(vec1==row)
                rowmatch = rowmatch*1
                
                colmatch = np.array(vec1==column)
                colmatch = colmatch*1
                
                match_matrix=rowmatch*colmatch.T
                target_mat=target_mat+(match_matrix*source_mat[row,column])
                
        print((time.time() - matrixtime))
        target_mat_fast=target_mat
        
        ### NEW FAST METHOD ###
        
        
#        TargetCell(i,j)=ClusterCell(labels(i),labels(j))
#        TargetCell(labels(2,i),labels(2,j)) = Cluster(labels(1,i),labels(1,j))
#        
#        #basic equation i want.
#        target_mat[vec2.iloc[vec,0],vec2.iloc[vec,0]]=source_mat[vec2.iloc[range(1,300),1],vec2.iloc[range(1,300),1]]
#        target_mat[vec2.iloc[vec,0],vec2.iloc[vec,0]]=source_mat[vec2.iloc[vec,1],vec2.iloc[vec,1]]
#
#
#        #Test Equivalence
#        target_mat_slow==target_mat_fast
        
        
        #%%#ALL SOLUTIONS
        import time
        import random
        import pandas as pd
        import numpy as np
        
        n=13000
        k=2000
        i=0
        vec1=[]
        for x in range(0, n):
            vec1.append(random.randint(0, k-1))
            
        temp=np.random.random((k,k))
        #vec1=pd.DataFrame(vec1)
        vec1=np.array(vec1)
        #vec=pd.DataFrame(np.arange(0,300))
        #vec2=pd.concat([vec,vec1], axis=1)
        #sizevec1=vec1.shape[0]
        sizevec1=len(vec1)
        matshape=(sizevec1,sizevec1)
        target_mat=np.zeros(matshape)
        #target_mat=pd.DataFrame(target_mat)
        
        
        source_mat=temp*temp.T
        transform_mat=np.zeros((len(source_mat),len(target_mat)))
        
        #%%Slow Solution
        matrixtime = time.time()
        for row in range(0,target_mat.shape[0]):
            #print 'row is ', row
            for column in range(0,target_mat.shape[1]):
                
                #print 'column is', column
                target_mat[row,column] = source_mat.item(int(vec1[row]), int(vec1[column]))
        print((time.time() - matrixtime))
        target_mat_slow=target_mat
        target_mat=np.zeros(matshape)
        #%% XU MACKENZIE SOLUTION
        matrixtime = time.time()

        for i in range(0,len(target_mat)):
          transform_mat[vec1[i],i]=1
          
        temp=np.dot(source_mat,transform_mat)
        target_mat=np.dot(temp.T,transform_mat)
        target_mat_XM=target_mat
        target_mat=np.zeros(matshape)
        XM_time= time.time() - matrixtime
        print((time.time() - matrixtime))

        #%%Previous 'fast' solution 
        matrixtime = time.time()
        for row in range(0,source_mat.shape[0]):
            print('row is ', row)
            #for column in range(0, source_mat.shape[1]):
            for column in range(0, row):   
                rowmatch = np.array([vec1==row])
                rowmatch = rowmatch*1
                
                colmatch = np.array([vec1==column])
                colmatch = colmatch*1
                
                match_matrix=rowmatch*colmatch.T
                target_mat=target_mat+(match_matrix*source_mat[row,column])
                
        print((time.time() - matrixtime))
        target_mat_fast=target_mat
        target_mat=np.zeros(matshape)
        #%% TEST FOR EQUIVALENCE
        
        target_mat_slow==target_mat_fast
        target_mat_fast==target_mat_XM
        
        
        #%%
#        ###  MATT SOLUTION FROM STACK OVERFLOW
#        cimport numpy
#        from numpy import array, multiply, asarray, ndarray, zeros, dtype, int
#        cimport cython
#        from cython cimport view
#        from cython.parallel cimport prange #this is your OpenMP portion
#        from openmp cimport omp_get_max_threads #only used for getting the max # of threads on the machine
#        
#        @cython.boundscheck(False)
#        @cython.wraparound(False)
#        @cython.cdivision(True)
#        cpdef matrixops(int[::1] vec1, double[:,::1] source_mat, double[:,::1] target_mat):
#            cdef int[::1] match_matrix =zeros(vec1.shape[0], dtype=int)
#            cdef int[::1] rowmatch =zeros(vec1.shape[0], dtype=int)
#            cdef int[::1] colmatch =zeros(vec1.shape[0], dtype=int)
#            cdef int maxthreads = omp_get_max_threads()
#            cdef int row, column, i
#            # here's where you'd substitute 
#            # for row in prange(source_mat.shape[0], nogil=True, num_threads=maxthreads, schedule='static'): # to use all cores
#            for row in range(0,source_mat.shape[0]):
#                for column in range(0, source_mat.shape[1]):
#                #this is how to avoid the GIL
#                for i in range(vec1.shape[0]):
#                    rowmatch[i]=(row==vec1[i])
#        
#                for i in range(vec1.shape[0]):
#                    colmatch[i]=(column==vec1[i])
#                    # this part has to be modified to not call Python GIL functions like was done above
#                    match_matrix=multiply(rowmatch,colmatch.T)
#                    target_mat=target_mat+(multiply(match_matrix,source_mat[row,column]))
#        

        #%%
        
        
        
        
        for i in range(0,len(transform_mat)):
            print(sum(transform_mat[:,i]))
        
        
        #####
         
         
         
         
        source_mat_T=source_mat*transform_mat
        final=clusterT.T*T
        
        #DavidMAtrix Method-
        #multiply cluster matrix by the mask of the label-voxel mask matrix.
        #multiply the answer by the transpose of the same label-voxel matrix
        
          ###TingMethod###
          
          
        target_mat=np.zeros(matshape)
        #target_mat=pd.DataFrame(target_mat)
        
        matrixtime = time.time()
        for row in range(0,source_mat.shape[0]):
            print ('row is ', row)
            for column in range(1, row):
                
                rowmatch = np.array(vec1==row)
                rowmatch = rowmatch*1
                
                colmatch = np.array(vec1==column)
                colmatch = colmatch*1
                
                match_matrix=rowmatch*colmatch.T
                target_mat=target_mat+(match_matrix*source_mat[row,column])
                
        print((time.time() - matrixtime))
        target_mat_fast=target_mat
        
###############################STACK OVERFLOW SCRIPT##########################################
######################################################################################################
######################################################################################################
        C_mike[Y1_labels==row,Y1_labels==column] = ism[row,column]


        a=Y1_labels.shape[0]
        b=(a,a)
        C = np.zeros(b)
        C=pd.DataFrame(C)
        ism=ism_dataset[0]
        ismdf=pd.DataFrame(ism)
           # for ism in ism_dataset:
       #pseudocode general purpose- for every row,column position in C,  
       #fill it with the corresponding value within the same row,column position in
       # the ism matrix.
        for row in range(0, C.shape[0]):
            for column in range(0, C.shape[1]):
                #print 'row is ', row
                #print 'column is', column
                #tempfunc=ism.item(int(Y1_labels.iloc[row]),int(Y1_labels.iloc[column]))
                C.iloc[row,column] = ism.item(int(Y1_labels.iloc[row]),int(Y1_labels.iloc[column])) 
#       

        import numpy as np
        x = np.zeros((96,11,11,2,10),dtype=np.float64)
        y = np.array([0,10,20,30,40,50,60,70,80,90,100],dtype=np.float64)
        for i in range(x.shape[0]):
            x[i,:,:,0,0] = x[i,:,:,0,0].T
        #print x[0,:,:,0,0]
         
        def relabelcells(C,rows,columns):
            C.iloc[rows,columns] = ismdf.iloc(Y1_labels.iloc[:],Y1_labels.iloc[:]) 
            
        
        #doesnt work
        C.iloc[:,:]=ismdf.iloc[Y1_labels.iloc[:],Y1_labels.iloc[:]]
        #Rmethod
#        cols <- colnames(m1)[colnames(m1) %in% colnames(m2)]
#        rows <- rownames(m1)[rownames(m1) %in% rownames(m2)]
#        m1[rows, cols] <- m2[rows, cols]
        #take a look here:
#        https://stackoverflow.com/questions/18763717/assigning-to-multi-dimensional-array?noredirect=1&lq=1
#        https://stackoverflow.com/questions/18759931/fill-a-column-of-a-numpy-array-with-another-array
##        
        C.apply(relabelcells,rows,columns)
        #figure out how to use APPLYMAP here
        #ism_dataset[i] = individual_stability_matrix(blobs.T + 0.2*np.random.randn(blobs.shape[1], blobs.shape[0]), 10, 3, affinity_threshold = 0.0)
        
        #################################################################################
        #################################################################################

        f = home + '/Dropbox/1_Projects/1_Research/2_CMI_BG_DEV/1_BASC/Results/Testing/ism_dataset_%i.npy' % i
        ism_list.append(f)
        np.save(f, ism_dataset[i])

    print((time.time() - start))
    G, cluster_G, cluster_voxel_scores = group_stability_matrix(ism_list, dataset_bootstraps, n_clusters=n_clusters)
    #Need to figure out how to get low res cluster version outputted in normal space- or how to output 
   # ndarray_to_vol(cluster_G, roi_mask_file, sample_file, filename)
    #loop over cluster_voxel_scores[i] and save each cluster map to nifti file.

def test_basc():
    import glob, os
    g_string = '/home/data/Projects/nuisance_reliability_paper/working_dir_CPAC_order/resting_preproc/func_in_mnioutputs/fmri_mnioutputs/_session_id_NYU_TRT_session1_subject_id_sub*/_csf_threshold_0.4/_gm_threshold_0.2/_wm_threshold_0.66/_run_scrubbing_False/_nc_5/_selector_6.7/apply_warp/mapflow/_apply_warp0/residual_warp.nii.gz'
    roi_file = '/home/data/Projects/nuisance_reliability_paper/seed_files/basil_ganglia/LEFT_BG_3_numbered+tlrc..nii.gz'

    subjects_list = glob.glob(g_string)
    b = basc.create_basc()
    b.base_dir = os.getcwd()
    b.inputs.inputspec.roi = roi_file
    b.inputs.inputspec.subjects = subjects_list
    b.inputs.inputspec.n_clusters = 6
    b.inputs.inputspec.dataset_bootstraps = 10
    b.inputs.inputspec.timeseries_bootstraps = 1000
