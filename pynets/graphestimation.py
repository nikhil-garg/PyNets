# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 10:40:07 2017

@author: Derek Pisner
"""

import sys
import numpy as np
#warnings.simplefilter("ignore")
from nilearn.connectome import ConnectivityMeasure
from sklearn.covariance import GraphLassoCV
try:
    from brainiak.fcma.util import compute_correlation
except ImportError:
    pass

def get_conn_matrix(time_series, conn_model):
    if conn_model == 'corr':
        conn_measure = ConnectivityMeasure(kind='correlation')
        conn_matrix = conn_measure.fit_transform([time_series])[0]
    elif conn_model == 'corr_fast':
        try:
            conn_matrix = compute_correlation(time_series,time_series)
        except RuntimeError:
            print('Cannot run accelerated correlation computation due to a missing dependency. You need brainiak installed!')
    elif conn_model == 'partcorr':
        conn_measure = ConnectivityMeasure(kind='partial correlation')
        conn_matrix = conn_measure.fit_transform([time_series])[0]
    elif conn_model == 'cov' or conn_model == 'sps':
        ##Fit estimator to matrix to get sparse matrix
        estimator = GraphLassoCV()
        try:
            print("Fitting Lasso Estimator...")
            estimator.fit(time_series)
        except RuntimeError:
            print('Unstable Lasso estimation--Attempting to re-run by first applying shrinkage...')
            from sklearn.covariance import GraphLasso, empirical_covariance, shrunk_covariance
            emp_cov = empirical_covariance(time_series)
            for i in np.arange(0.8, 0.99, 0.01):
                shrunk_cov = shrunk_covariance(emp_cov, shrinkage=i)
                alphaRange = 10.0 ** np.arange(-8,0)
                for alpha in alphaRange:
                    try:
                        estimator_shrunk = GraphLasso(alpha)
                        estimator_shrunk.fit(shrunk_cov)
                        print("Calculated graph-lasso covariance matrix for alpha=%s"%alpha)
                        break
                    except FloatingPointError:
                        print("Failed at alpha=%s"%alpha)
                if estimator_shrunk == None:
                    pass
                else:
                    break
                print('Unstable Lasso estimation. Try again!')
                sys.exit()

        if conn_model == 'sps':
            try:
                conn_matrix = -estimator.precision_
            except:
                conn_matrix = -estimator_shrunk.precision_
        elif conn_model == 'cov':
            try:
                conn_matrix = estimator.covariance_
            except:
                conn_matrix = estimator_shrunk.covariance_

    return(conn_matrix)
