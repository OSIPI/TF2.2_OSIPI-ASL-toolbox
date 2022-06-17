 # -*- coding: utf-8 -*-
import argparse
import os, time, datetime
import numpy as np
from tensorflow.keras.models import load_model, model_from_json
from skimage.measure import compare_psnr, compare_ssim
from skimage.io import imread, imsave
import scipy.misc
import os
import tensorflow as tf
import glob
import imageio
import nibabel as nib
#from keras import load_weights
import Mymodel
#from keras.models import load_model
#import nibabel as nib
os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
# The GPU id to use, usually either "0" or "1"; 0 is 980TI, 1 is Titan X
os.environ["CUDA_VISIBLE_DEVICES"]="0"
def parse_args():
    parser = argparse.ArgumentParser()    
    parser.add_argument('--model_dir', default=os.path.join('../models','DWAN_huber_loss_ft_ADNI_All_0630'), type=str, help='directory of the model')    
    parser.add_argument('--model_name', default='model_099.hdf5', type=str, help='the model name')
    return parser.parse_args()

def get_subj_c123(subj,folder='E:\DualEcho',use_c3 = True):
    c1 = nib.load(glob.glob(folder+'/{}/ANAT_DL_mask/rbk_c1*.nii'.format(subj))[0])
    c2 = nib.load(glob.glob(folder+'/{}/ANAT_DL_mask/rbk_c2*.nii'.format(subj))[0])   
    if use_c3:
        c3 = nib.load(glob.glob(folder+'/{}/ANAT_DL_mask/rbk_c3*.nii'.format(subj))[0])
        c123 = c1.get_data()+c2.get_data()+c3.get_data()
    else:
        c123 = c1.get_data()+c2.get_data()
    print(c123.shape)
    return c123

def read_subject_list(path):
    with open(path) as f:
        sublist = f.readlines()
    content = []
    for item in sublist:
        content.append(item.rstrip())
    return content
        
if __name__ == '__main__':    
    
    args = parse_args()   
    model = Mymodel.dilated_net_wide(3)   
    model.load_weights(os.path.join(args.model_dir, args.model_name))   
    print(os.path.join(args.model_dir, args.model_name))   
    print('model loaded')

    def predict_nii_meancbf_w_masks_rbk(model,root_folder,save_name):
        content = read_subject_list('{}subjectlist_valid.txt'.format(root_folder))
        mask_folder = root_folder
        for i in range(len(content)):
            print(i, content[i], save_name)
            item_path = glob.glob('{}/{}/ASL/cmeanCBF_cleaned*.nii'.format(root_folder,content[i]))[0]
            item_obj = nib.load(item_path)
            item = item_obj.get_data()
            mask = get_subj_c123(content[i],mask_folder)            
            item[np.isnan(item)] = 0.0
            item[np.isinf(item)] = 0.0                
            mask[np.isnan(mask)] = 0.0
            mask[np.isinf(mask)] = 0.0            
            #for Relu updating.
            item[mask[:,:,:] < 0.1] = 2                            
            y = np.clip(item,0,150)/255.0           
            y_ = np.transpose(y,(2,0,1))            
            y_ = y.reshape((y.shape[0],y.shape[1],y.shape[2],1))
            x_ = model.predict(y_)            
            x_ = np.clip(np.squeeze(x_*255.0),0,150)                                              
            mask_nii = nib.Nifti1Image(mask, item_obj.affine, item_obj.header)                              
            mask[mask>0] = 1                 
            print(np.unique(mask), content[i])
            x_ = x_ * mask            
            x_nii = nib.Nifti1Image(x_, item_obj.affine, item_obj.header)                        
            save_path_bin = '{}/{}/ASL/{}.nii'.format(root_folder,content[i],save_name + '_w_bin_mask')
            nib.save(x_nii,save_path_bin)
            
    save_name = 'ADNI_JMRI_R1_0630'
    predict_nii_meancbf_w_masks_rbk(model,'../data/',save_name)
    
    
    