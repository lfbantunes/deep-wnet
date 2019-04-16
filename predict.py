from __future__ import print_function
import math
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import tifffile as tiff
from train_unet import weights_path, get_model, PATCH_SZ, N_CLASSES
from scipy import stats
from sklearn.metrics import classification_report, accuracy_score
import gc
from skimage.util.shape import view_as_windows
import time
from itertools import product
import numbers
from sklearn.feature_extraction import image
from patchify import patchify, unpatchify
from numpy.lib.stride_tricks import as_strided


def reconstruct_patches(patches, image_size, step):
    i_h, i_w = image_size[:2]
    p_h, p_w = patches.shape[1:3]
    img = np.zeros(image_size)
    patch_count = np.zeros(image_size)
    # compute the dimensions of the patches array
    n_h = int((i_h - p_h) / step + 1)
    n_w = int((i_w - p_w) / step + 1)
    for p, (i, j) in zip(patches, product(range(n_h), range(n_w))):
        img[i * step:i * step + p_h, j * step:j * step + p_w] += p
    #for p, (i, j) in zip(patches, product(range(n_h), range(n_w))):
        patch_count[i * step:i * step + p_h, j * step:j * step + p_w] += 1
    print('MAX time seen', np.amax(patch_count))
    return img/patch_count

def predict(x, model, patch_sz=160, n_classes=5, step = 142):
    dim_x, dim_y, dim = x.shape
    patches = patchify(x, (patch_sz, patch_sz, x.ndim), step = step)
    width_window, height_window, z, width_x, height_y, num_channel = patches.shape
    patches = np.reshape(patches, (width_window * height_window,  width_x, height_y, num_channel))

    patches_predict = model.predict(patches, batch_size=4)

    prediction = reconstruct_patches(patches_predict, (dim_x, dim_y, n_classes), step)

    return prediction


def picture_from_mask(mask):
    colors = {
        0: [255, 255, 255],   #imp surface
        1: [255, 255, 0],     #car
        2: [0, 0, 255],       #building
        3: [255, 0, 0],       #background
        4: [0, 255, 255],     #low veg
        5: [0, 255, 0]        #tree
    }

    mask_ind = np.argmax(mask, axis=0)
    pict = np.empty(shape=(3, mask.shape[1], mask.shape[2]))
    for cl in range(6):
      for ch in range(3):
        pict[ch,:,:] = np.where(mask_ind == cl, colors[cl][ch], pict[ch,:,:])
    return pict

def mask_from_picture(picture):
  colors = {
      (255, 255, 255): 0,   #imp surface
      (255, 255, 0): 1,     #car
      (0, 0, 255): 2,       #building
      (255, 0, 0): 3,       #background
      (0, 255, 255): 4,     #low veg
      (0, 255, 0): 5        #tree
  }
  picture = picture.transpose([1,2,0])
  mask = np.ndarray(shape=(256*256*256), dtype='int32')
  mask[:] = -1
  for rgb, idx in colors.items():
    rgb = rgb[0] * 65536 + rgb[1] * 256 + rgb[2]
    mask[rgb] = idx

  picture = picture.dot(np.array([65536, 256, 1], dtype='int32'))
  return mask[picture]

def predict_all(step, dataset):
    model = get_model()
    model.load_weights(weights_path)
    if dataset == 'p':
        test = ['2_13','2_14','3_13','3_14','4_13','4_14','4_15','5_13','5_14','5_15','6_13','6_14','6_15','7_13']
        dir_img = './potsdam/Images_lab/top_potsdam_{}_RGB.tif'
        dir_mask = './potsdam/Masks/top_potsdam_{}_label.tif'
    accuracy_all = []
    for test_id in test:
        path_img = dir_img.format(test_id)
        img = tiff.imread(path_img)
        path_mask = dir_mask.format(test_id)
        label = tiff.imread(path_mask).transpose([2,0,1])
        gt = mask_from_picture(label)

        mask = predict(img, model, patch_sz=PATCH_SZ, n_classes=N_CLASSES, step = step).transpose([2,0,1])

        prediction = picture_from_mask(mask)

        target_labels = ['imp surf', 'car', 'building', 'background', 'low veg', 'tree']
        y_true = gt.ravel()
        y_pred = np.argmax(mask, axis=0).ravel()
        report = classification_report(y_true, y_pred, target_names = target_labels)
        accuracy = accuracy_score(y_true, y_pred)
        print('\n',test_id)
        print(report)
        print('\nAccuracy', accuracy)
        accuracy_all.append(accuracy)
        tiff.imsave('./results/map_{}.tif'.format(test_id), prediction)
        gc.collect()
        gc.collect()
        gc.collect()
        sys.stdout.flush()

    print(accuracy_all)
    print(step,' Accuracy all', sum(accuracy_all)/len(accuracy_all))



'8'
predict_all(284, 'p')