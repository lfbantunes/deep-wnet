import numpy as np
from gen_patches import *
import tifffile as tiff
import os
from os import listdir
from os.path import isfile, join

def get_input(path):
    #image = rasterio.open(path).read().transpose([1,2,0])
    image = tiff.imread(path)
    return image

def get_mask(path):
    mask = tiff.imread(path)
    return mask

def image_generator(ids_file, path_image, path_mask, path_full_img, batch_size = 5, patch_size = 160):
    ids_file_all = ids_file[:]
    while True:
        if not ids_file:
            ids_file = ids_file_all[:]
        id = ids_file.pop(np.random.choice(len(ids_file)))
        image = get_input(path_image.format(id))
        mask = get_mask(path_mask.format(id))
        full_img = get_input(path_full_img.format(id))
        total_patches = 0
        x = list()
        y = list()
        y2 = list()
        while total_patches < batch_size:
            img_patch, mask_patch, full_img_patch = get_rand_patch(image, mask, full_img, patch_size)
            x.append(img_patch)
            y.append(mask_patch)
            y2.append(full_img_patch)
            total_patches += 1

        batch_x = np.array( x )
        batch_y = np.array( y )
        batch_y2 = np.array( y2 )
        yield ( batch_x, [batch_y , batch_y2])
        #yield ( batch_x, batch_y )


def val_generator(path_patch_img, path_patch_full_img, path_patch_mask, batch_size = 5):
    files = [f for f in listdir(path_patch_img) if isfile(join(path_patch_img, f))]
    n=0
    while True:
        total_patches = 0
        x = list()
        y = list()
        y2 = list()
        while total_patches < batch_size:
            n+=1
            print(n)
            file = files.pop()
            x.append(get_input(path_patch_img+file))
            y.append(get_input(path_patch_mask+file))
            y2.append(get_input(path_patch_full_img+file))
            total_patches += 1
        batch_x = np.array(x)
        batch_y = np.array(y)
        batch_y2 = np.array(y2)
        yield (batch_x, [batch_y, batch_y2])
