# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 10:34:08 2023

@author: saeid
"""

import os.path
import numpy as np
import matplotlib.pyplot as plt
import scipy
import math
import pandas as pd
import tensorflow as tf
import numpy as np
from tensorflow import keras
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from refnx.analysis import Parameter, Model
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import SGD
from time import time
import random


import refnx
from refnx.dataset import ReflectDataset, Data1D
from refnx.analysis import Transform, CurveFitter, Objective, Model, Parameter
from refnx.reflect import SLD, Slab, ReflectModel

import keras

plt.rcParams['figure.dpi'] = 900
plt.rcParams['savefig.dpi'] = 900


q_values = np.linspace(0.01, 0.6 , 1024)

import tensorflow as tf
import numpy as np
from random import sample
import pandas as pd
import matplotlib.pyplot as plt

import joblib
import pickle


modelf = joblib.load('/home/kowarik/Documents/Saeid/Data/Models/RandomForestReg/random_forest_regressor_1024.joblib')

autoencoder_model=tf.keras.models.load_model('/home/kowarik/Documents/Saeid/Data/Models/AutoEncoder/Autoencoder_fit_1024.h5')
parameters_model=tf.keras.models.load_model('/home/kowarik/Documents/Saeid/Data/Models/NN_model/trained_model_all_parameters_1024.h5')



def Fit_Thick(X,q_values,Z):
    result=[]
    non_zero_idx=np.where(X!=0)
    Y=np.concatenate(([q_values[non_zero_idx]], [X[non_zero_idx]]), axis=0)
    air = SLD(0-0j, name='first')
    s= air(0,1)
    structure=s
    labl="Layer"
    tmp_var=1j
    k=Z[-2]+Z[-1]*tmp_var
    w=SLD(k, name=labl)
    midl_layer=w(Z[-4],Z[-3])
    structure=structure|midl_layer

    si = SLD(20-0.1j, name='last')
    s = si(0,0)
    structure=structure|s
    model = ReflectModel(structure, bkg=3e-9, dq=0)
    midl_layer.sld.real.setp(bounds=(1e-3,300), vary=True)
    midl_layer.sld.imag.setp(bounds=(-20, -1e-3), vary=True)
    midl_layer.thick.setp(bounds=(20,400), vary=True)
    midl_layer.rough.setp(bounds=(1e-3,60), vary=True)
    model.bkg.setp(bounds=(1e-9, 9e-6), vary=True)
    #model.dq.setp(bounds=(1e-3,5),vary=True)
    objective = Objective(model, Y, transform=Transform('logY'))

    fitter = CurveFitter(objective)
    fitter.fit('differential_evolution');
    result.append(objective.parameters['Structure - ']['Layer']['Layer - thick'].value)
    result.append(objective.parameters['Structure - ']['Layer']['Layer - rough'].value)
    result.append(objective.parameters['Structure - ']['Layer']['Layer']['Layer - sld'].value)
    result.append(objective.parameters['Structure - ']['Layer']['Layer']['Layer - isld'].value)
    return result

X=list(range(1024))
importances = modelf.feature_importances_
data=pd.DataFrame()
data["parameter"]=[str(x) for x in X]
data["weights"]=importances
data=data.sort_values(by=['weights'], ascending=False)

c=sample(range(100000),1000)
data_list = []

for i in range(100):
    filename = f"/home/kowarik/Documents/Saeid/Data/Sim_data_{i}_w.csv"
    datac = np.loadtxt(filename, delimiter=",")
    data_list.append(datac)
    print(i)

concatenated_data = np.concatenate(data_list, axis=0)
dat=pd.DataFrame(concatenated_data)
X = dat.iloc[:,:].values

mi=[]
ma=[]
for i in range(len(X[0])-4):
    mi.append(X[:,i].min())
    ma.append(X[:,i].max())

data1=pd.DataFrame(X)

train, validate, test = np.split(data1.sample(frac=1, random_state=42),[int(.8*len(data1)), int(.9*len(data1))])
X_train=train.iloc[:,:-4].values
y_train=train.iloc[:,-4:].values
y_train[:,-1]=y_train[:,-1]*-1
X_valid=validate.iloc[:,:-4].values
y_valid=validate.iloc[:,-4:].values
y_valid[:,-1]=y_valid[:,-1]*-1
X_test=test.iloc[:,:-4].values
y_test=test.iloc[:,-4:].values
y_test[:,-1]=y_test[:,-1]*-1

Tmp=X_test[c,:].copy()
New_X=(np.array(Tmp)-np.array(mi))/(np.array(ma)-np.array(mi))

Error_RFR=[]
Error_RFRNN=[]
Error_RFRWO=[]
Error_Rand=[]
Error_RandNN=[]
Error_RandWO=[]
Error_Eq=[]
Error_EqNN=[]
Error_EqWO=[]
Acc_RFR=[]
Acc_RFRNN=[]
Acc_RFRWO=[]
Acc_Rand=[]
Acc_RandNN=[]
Acc_RandWO=[]
Acc_Eq=[]
Acc_EqNN=[]
Acc_EqWO=[]

Ground_truth=parameters_model.predict([New_X.reshape(1000, 1024)])

Tmp=y_test[c,:].copy()
Ground_truth1=Tmp
Ground_truth1[:,-1]=Ground_truth1[:,-1]*-1
Ground_truth[:,-1]=Ground_truth[:,-1]*-1

List_to_eval=sample(range(1000),500)

flag2=56

for test_data_to_fit in List_to_eval[57:500]:
    if test_data_to_fit == List_to_eval[0]:
        flag2 = 0
    else:
        flag2=flag2+1
    ErrorRand=[]
    ErrorRandNN=[]
    ErrorRandWO=[]
    ErrorRFR=[]
    ErrorRFRNN=[]
    ErrorRFRWO=[]
    ErrorEq=[]
    ErrorEqNN=[]
    ErrorEqWO=[]


    tree_index=0
    tree = modelf.estimators_[tree_index]
    res = [eval(i) for i in data["parameter"]]
    for j in range(256):
        tree_index = 0
        node_index = 0
        next_node=0
        flag=0
        sol_index=list(map(int,list(np.arange(0,1024,1024/(4*(j+1))))))
        New_X=X_test[c[test_data_to_fit],:].copy()
        New_X[list(set(range(1024)) - set(sol_index))]=math.nan
        New_X=(np.array(New_X)-np.array(mi))/(np.array(ma)-np.array(mi))
        New_X[[math.isnan(x) for x in New_X]] = 0 # replace NaN values with zeros
        predicted_list = autoencoder_model.predict(New_X.reshape(1, -1))
        predicted_list[predicted_list < 0] = 0 # replace negative values with zeros
        predicted_list = predicted_list.flatten()
        Tmp=Fit_Thick(predicted_list,q_values,Ground_truth1[test_data_to_fit,:])
        ErrorEq.append(abs(np.array(Ground_truth1[test_data_to_fit])-np.array(Tmp)))
        Tmp=parameters_model.predict([predicted_list.reshape(1, 1024)])
        initial_params = Tmp[0]
        initial_params[-1]=initial_params[-1]*-1
        y_true = X_test[c[test_data_to_fit],sol_index].copy()
        q_val = q_values[sol_index]
        def mean_square_error(y_pred):
            thicknesses1, roughnesses1, SLDs_real1, SLDs_img1 = y_pred
            y_predicted = predicted_curve(q_val, thicknesses1, roughnesses1, SLDs_real1, SLDs_img1)
            mse = np.mean((y_true - y_predicted) ** 2)
            return mse
        Tmp = minimize(mean_square_error, initial_params, method='Nelder-Mead')
        ErrorEqNN.append(abs(np.array(Ground_truth1[test_data_to_fit])-np.array(Tmp.x)))
        New_X=X_test[c[test_data_to_fit],:].copy()
        New_X[list(set(range(1024)) - set(sol_index))]=math.nan
        New_X[[math.isnan(x) for x in New_X]] = 0 # replace NaN values with zeros
        Tmp=Fit_Thick(New_X,q_values,Ground_truth1[test_data_to_fit,:])
        ErrorEqWO.append(abs(np.array(Ground_truth1[test_data_to_fit])-np.array(Tmp)))
        print(f"{j} from {flag2} is done!!...")
    print(f"{c[test_data_to_fit]}--Eq-dist {flag2} is Done!!...")
    
    for j in range(256):
        tree_index = 0
        node_index = 0
        next_node=0
        flag=0
        sol_index=[res[counter] for counter in range(4*(j+1))]
        New_X=X_test[c[test_data_to_fit],:].copy()
        New_X[list(set(range(1024)) - set(sol_index))]=math.nan
        New_X=(np.array(New_X)-np.array(mi))/(np.array(ma)-np.array(mi))
        New_X[[math.isnan(x) for x in New_X]] = 0 # replace NaN values with zeros
        predicted_list = autoencoder_model.predict(New_X.reshape(1, -1))
        predicted_list[predicted_list < 0] = 0 # replace negative values with zeros
        predicted_list = predicted_list.flatten()
        Tmp=Fit_Thick(predicted_list,q_values,Ground_truth1[test_data_to_fit,:])
        ErrorRFR.append(abs(np.array(Ground_truth1[test_data_to_fit])-np.array(Tmp)))
        Tmp=parameters_model.predict([predicted_list.reshape(1, 1024)])
        initial_params = Tmp[0]
        initial_params[-1]=initial_params[-1]*-1
        y_true = X_test[c[test_data_to_fit],sol_index].copy()
        q_val = q_values[sol_index]
        def mean_square_error(y_pred):
            thicknesses1, roughnesses1, SLDs_real1, SLDs_img1 = y_pred
            y_predicted = predicted_curve(q_val, thicknesses1, roughnesses1, SLDs_real1, SLDs_img1)
            mse = np.mean((y_true - y_predicted) ** 2)
            return mse
        Tmp = minimize(mean_square_error, initial_params, method='Nelder-Mead')
        ErrorRFRNN.append(abs(np.array(Ground_truth1[test_data_to_fit])-np.array(Tmp.x)))
        New_X=X_test[c[test_data_to_fit],:].copy()
        New_X[list(set(range(1024)) - set(sol_index))]=math.nan
        New_X[[math.isnan(x) for x in New_X]] = 0 # replace NaN values with zeros
        Tmp=Fit_Thick(New_X,q_values,Ground_truth1[test_data_to_fit,:])
        ErrorRFRWO.append(abs(np.array(Ground_truth1[test_data_to_fit])-np.array(Tmp)))
        print(f"{j} from {flag2} is done!!...")
    print(f"{c[test_data_to_fit]}--RFR {flag2} is Done!!...")
    
    for j in range(256):
        tree_index = 0
        node_index = 0
        next_node=0
        flag=0
        sol_index=sample(list(range(1024)),4*(j+1))
        New_X=X_test[c[test_data_to_fit],:].copy()
        New_X[list(set(range(1024)) - set(sol_index))]=math.nan
        New_X=(np.array(New_X)-np.array(mi))/(np.array(ma)-np.array(mi))
        New_X[[math.isnan(x) for x in New_X]] = 0 # replace NaN values with zeros
        predicted_list = autoencoder_model.predict(New_X.reshape(1, -1))
        predicted_list[predicted_list < 0] = 0 # replace negative values with zeros
        predicted_list = predicted_list.flatten()
        Tmp=Fit_Thick(predicted_list,q_values,Ground_truth1[test_data_to_fit,:])
        ErrorRand.append(abs(np.array(Ground_truth1[test_data_to_fit])-np.array(Tmp)))
        Tmp=parameters_model.predict([predicted_list.reshape(1, 1024)])
        initial_params = Tmp[0]
        initial_params[-1]=initial_params[-1]*-1
        y_true = X_test[c[test_data_to_fit],sol_index].copy()
        q_val = q_values[sol_index]
        def mean_square_error(y_pred):
            thicknesses1, roughnesses1, SLDs_real1, SLDs_img1 = y_pred
            y_predicted = predicted_curve(q_val, thicknesses1, roughnesses1, SLDs_real1, SLDs_img1)
            mse = np.mean((y_true - y_predicted) ** 2)
            return mse
        Tmp = minimize(mean_square_error, initial_params, method='Nelder-Mead')
        ErrorRandNN.append(abs(np.array(Ground_truth1[test_data_to_fit])-np.array(Tmp.x)))
        New_X=X_test[c[test_data_to_fit],:].copy()
        New_X[list(set(range(1024)) - set(sol_index))]=math.nan
        New_X[[math.isnan(x) for x in New_X]] = 0 # replace NaN values with zeros
        Tmp=Fit_Thick(New_X,q_values,Ground_truth1[test_data_to_fit,:])
        ErrorRandWO.append(abs(np.array(Ground_truth1[test_data_to_fit])-np.array(Tmp)))
        print(f"{j} from {flag2} is done!!...")
    print(f"{c[test_data_to_fit]}--Random {flag2} is Done!!...")
    
    p2=np.array(ErrorRand.copy())
    pNN2=np.array(ErrorRandNN.copy())
    pWO2=np.array(ErrorRandWO.copy())
    np2=p2.copy()
    p1=np.array(ErrorRFR.copy())
    pNN1=np.array(ErrorRFRNN.copy())
    pWO1=np.array(ErrorRFRWO.copy())
    p3=np.array(ErrorEq.copy())
    pNN3=np.array(ErrorEqNN.copy())
    pWO3=np.array(ErrorEqWO.copy())
    np1=p1.copy()
    for i in range(4):
        max_t=max(np1[:,i])
        np1[:,i]=np1[:,i]/max_t
    npNN1=pNN1.copy()
    for i in range(4):
        max_t=max(npNN1[:,i])
        npNN1[:,i]=npNN1[:,i]/max_t
    npWO1=pWO1.copy()
    for i in range(4):
        max_t=max(npWO1[:,i])
        npWO1[:,i]=npWO1[:,i]/max_t
    np3=p3.copy()
    for i in range(4):
        max_t=max(p3[:,i])
        np3[:,i]=np3[:,i]/max_t
    npNN3=pNN3.copy()
    for i in range(4):
        max_t=max(pNN3[:,i])
        npNN3[:,i]=npNN3[:,i]/max_t
    npWO3=pWO3.copy()
    for i in range(4):
        max_t=max(pWO3[:,i])
        npWO3[:,i]=npWO3[:,i]/max_t
    for i in range(4):
        max_t=max(p2[:,i])
        np2[:,i]=np2[:,i]/max_t
    npNN2=pNN2.copy()
    for i in range(4):
        max_t=max(pNN2[:,i])
        npNN2[:,i]=npNN2[:,i]/max_t
    npWO2=pWO2.copy()
    for i in range(4):
        max_t=max(pWO2[:,i])
        npWO2[:,i]=npWO2[:,i]/max_t
    rnp1=1-np.mean(np.power(np1, 2), axis=1)
    rnpNN1=1-np.mean(np.power(npNN1, 2), axis=1)
    rnpWO1=1-np.mean(np.power(npWO1, 2), axis=1)
    rnp3=1-np.mean(np.power(np3, 2), axis=1)
    rnpNN3=1-np.mean(np.power(npNN3, 2), axis=1)
    rnpWO3=1-np.mean(np.power(npWO3, 2), axis=1)

    rnp2=1-np.mean(np.power(np2, 2), axis=1)
    rnpNN2=1-np.mean(np.power(npNN2, 2), axis=1)
    rnpWO2=1-np.mean(np.power(npWO2, 2), axis=1)
    if flag2 == 0:
        Error_Rand=ErrorRand.copy()
        Error_RandNN=ErrorRandNN.copy()
        Error_RandWO=ErrorRandWO.copy()
        Acc_Rand=rnp2.copy()
        Acc_RandNN=rnpNN2.copy()
        Acc_RandWO=rnpWO2.copy()
        Error_RFR=ErrorRFR.copy()
        Error_RFRNN=ErrorRFRNN.copy()
        Error_RFRWO=ErrorRFRWO.copy()
        Error_Eq=ErrorEq.copy()
        Error_EqNN=ErrorEqNN.copy()
        Error_EqWO=ErrorEqWO.copy()
        Acc_RFR=rnp1.copy()
        Acc_RFRNN=rnpNN1.copy()
        Acc_RFRWO=rnpWO1.copy()
        Acc_Eq=rnp3.copy()
        Acc_EqNN=rnpNN3.copy()
        Acc_EqWO=rnpWO3.copy()
    else:
        Error_Rand=np.array(Error_Rand)+np.array(ErrorRand.copy())
        Error_RandNN=np.array(Error_RandNN)+np.array(ErrorRandNN.copy())
        Error_RandWO=np.array(Error_RandWO)+np.array(ErrorRandWO.copy())
        Acc_Rand=np.array(Acc_Rand)+np.array(rnp2.copy())
        Acc_RandNN=np.array(Acc_RandNN)+np.array(rnpNN2.copy())
        Acc_RandWO=np.array(Acc_RandWO)+np.array(rnpWO2.copy())
        Error_Eq=np.array(Error_Eq)+np.array(ErrorEq.copy())
        Error_EqNN=np.array(Error_EqNN)+np.array(ErrorEqNN.copy())
        Error_EqWO=np.array(Error_EqWO)+np.array(ErrorEqWO.copy())
        Acc_Eq=np.array(Acc_Eq)+np.array(rnp3.copy())
        Acc_EqNN=np.array(Acc_EqNN)+np.array(rnpNN3.copy())
        Acc_EqWO=np.array(Acc_EqWO)+np.array(rnpWO3.copy())
        Error_RFR=np.array(Error_RFR)+np.array(ErrorRFR.copy())
        Error_RFRNN=np.array(Error_RFRNN)+np.array(ErrorRFRNN.copy())
        Error_RFRWO=np.array(Error_RFRWO)+np.array(ErrorRFRWO.copy())
        Acc_RFR=np.array(Acc_RFR)+np.array(rnp1.copy())
        Acc_RFRNN=np.array(Acc_RFRNN)+np.array(rnpNN1.copy())
        Acc_RFRWO=np.array(Acc_RFRWO)+np.array(rnpWO1.copy())
    print(f"{c[test_data_to_fit]} is {flag2}th and done!!!...")
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_RFR.csv', Error_RFR, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_RFRNN.csv', Error_RFRNN, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_RFRWO.csv', Error_RFRWO, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_Rand.csv', Error_Rand, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_RandNN.csv', Error_RandNN, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_RandWO.csv', Error_RandWO, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_Eq.csv', Error_Eq, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_EqNN.csv', Error_EqNN, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_EqWO.csv', Error_EqWO, delimiter=',')

    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_RFR.csv', Acc_RFR, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_RFRNN.csv', Acc_RFRNN, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_RFRWO.csv', Acc_RFRWO, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_Rand.csv', Acc_Rand, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_RandNN.csv', Acc_RandNN, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_RandWO.csv', Acc_RandWO, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_Eq.csv', Acc_Eq, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_EqNN.csv', Acc_EqNN, delimiter=',')
    np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_EqWO.csv', Acc_EqWO, delimiter=',')







Error_Rand=Error_Rand/65
Error_RandNN=Error_RandNN/65
Error_RandWO=Error_RandWO/65

Acc_Rand=Acc_Rand/65
Acc_RandNN=Acc_RandNN/65
Acc_RandWO=Acc_RandWO/65

Error_RFR=Error_RFR/65
Error_RFRNN=Error_RFRNN/65
Error_RFRWO=Error_RFRWO/65

Acc_Eq=Acc_Eq/65
Acc_EqNN=Acc_EqNN/65
Acc_EqWO=Acc_EqWO/65

Error_Eq=Error_Eq/65
Error_EqNN=Error_EqNN/65
Error_EqWO=Error_EqWO/65

Acc_RFR=Acc_RFR/65
Acc_RFRNN=Acc_RFRNN/65
Acc_RFRWO=Acc_RFRWO/65

np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_RFR.csv', Error_RFR, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_RFRNN.csv', Error_RFRNN, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_RFRWO.csv', Error_RFRWO, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_Rand.csv', Error_Rand, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_RandNN.csv', Error_RandNN, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_RandWO.csv', Error_RandWO, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_Eq.csv', Error_Eq, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_EqNN.csv', Error_EqNN, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Error_1024_EqWO.csv', Error_EqWO, delimiter=',')

np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_RFR.csv', Acc_RFR, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_RFRNN.csv', Acc_RFRNN, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_RFRWO.csv', Acc_RFRWO, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_Rand.csv', Acc_Rand, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_RandNN.csv', Acc_RandNN, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_RandWO.csv', Acc_RandWO, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_Eq.csv', Acc_Eq, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_EqNN.csv', Acc_EqNN, delimiter=',')
np.savetxt('/home/kowarik/Documents/Saeid/Data/Models/Results/Acc_1024_EqWO.csv', Acc_EqWO, delimiter=',')

test_data_to_fit = 0

p1 = np.array(ErrorEqNN)
p2 = np.array(ErrorEqWO)
p3 = np.array(ErrorRFRNN)
p4 = np.array(ErrorRFRWO)
plt.plot(range(30),p1[:,test_data_to_fit])
plt.plot(range(30),p2[:,test_data_to_fit])
plt.plot(range(30),p3[:,test_data_to_fit])
plt.plot(range(30),p4[:,test_data_to_fit])
plt.legend(["NN","Refnx WO","RFRNN","RFRRefnx"])

