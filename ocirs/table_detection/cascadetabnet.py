'''
This python file is a draft of what the CascadeTabNet table detection and crop
process should look like. 

The functions and environment are pulled directly from this jupyter notebook:
https://colab.research.google.com/drive/1EcyTPPWbZrIEJqRcVf61VxjU6pKd3gOX?usp=sharing

There are several environmental dependencies necessary for the below functions to work:


!pip install torch==1.4.0+cu100 torchvision==0.5.0+cu100 -f https://download.pytorch.org/whl/torch_stable.html
!pip install -q mmcv terminaltables
!git clone --branch v1.2.0 'https://github.com/open-mmlab/mmdetection.git'
%cd "mmdetection"
!pip install -r "/content/mmdetection/requirements/optional.txt"
!python setup.py install
!python setup.py develop
!pip install -r {"requirements.txt"}
!pip install pillow==6.2.1 
!pip install mmcv==0.4.3

%cd "/content"
!git clone https://github.com/DevashishPrasad/CascadeTabNet.git

The environmental setup and the functions below will look slightly different on a local machine as opposed to a Google colab file. 
Adjust process accordingly
'''

from mmdet.apis import init_detector, inference_detector
import cv2

import os
from os.path import dirname, realpath
pwd = dirname(realpath(__file__))
config_file_path = realpath(os.path.join(pwd, 'config', 'cascade_mask_rcnn_hrnetv2p_w32_20e.py'))
checkpoint_file_path = realpath(os.path.join(pwd, 'model_checkpoint', 'epoch_36.pth'))

def cascadetabnet_crop_table(model, image):
    '''
    crop_form will be the main function for the cascadeTabNet process, taking in a file (img) and returning a list of tuples each representing a detected table
    Each tuple consists of two components. First a numpy-array representation of the cropped table image. Second an assertion of whether the table is bordered or borderless 
    '''

    result = table_bounds(model, image)

    table_imgs = table_crop(image, result)

    return table_imgs


def define_model(config_file_path=config_file_path, checkpoint_file_path=checkpoint_file_path):
  
    model = init_detector(config_file_path, checkpoint_file_path, device='cuda:0')

    return model

def table_bounds(model, image):


    result = inference_detector(model, image)

    return result


def table_crop(image, result):

    table_imgs = [] #List containting all images of detected tables
    
    res_border = []
    res_bless = []
    res_cell = []


    # for border
    for r in result[0][0]:
        if r[4]>.85:
            res_border.append(r[:4].astype(int))
    # for cells
    for r in result[0][1]:
        if r[4]>.85:
            r[4] = r[4]*100
            res_cell.append(r.astype(int))
    # for borderless
    for r in result[0][2]:
        if r[4]>.85:
            res_bless.append(r[:4].astype(int))

    # if border tables detected 
    # call border script for each table in image
    for no, res in enumerate(res_border):
        
        # print(image.shape)

        #These is a consistent tight crop on certain bordered tables that we are looking at 
        #The padding calculated here is a dumb solution to temporarily fix it
        x_padding = int(image.shape[1]/100) if res[0]-int(image.shape[1]/100) > 0 else 0

        bordered_table_cropped = image[res[1]:res[3], res[0]-x_padding:res[2]] #The cropping png this does not appear to work perfectly. May need some additional padding. [y:y+h, x:x+w]
        
        table_imgs.append((bordered_table_cropped, "bordered"))

        
        # if borderless tables detected
    # call borderless script for each table in image
    for no, res in enumerate(res_bless):
        
        borderless_table_cropped = image[res[1]:res[3], res[0]:res[2]]
        
        table_imgs.append((borderless_table_cropped,"borderless"))


    return table_imgs



if __name__ =="__main__":

    
    model = define_model()

    image_path = realpath(os.path.join(pwd, 'test_image.jpg'))

    # image_path = "ocirs/table_detection/test_image.jpg"
    image = cv2.imread(image_path)
    
    table_imgs = cascadetabnet_crop_table(model, image)

    cv2.imwrite("test_output.jpg",table_imgs[0][0])