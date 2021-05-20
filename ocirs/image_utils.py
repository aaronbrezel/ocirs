import re
import cv2
import pytesseract
import numpy as np



def table_preprocess(image):
    '''
    Loads an image from path using cv2
    Uses pytesseract to rotate image to correct orientation
    Greyscales the rotated image
    And threshold the image to binary values
    '''

    #Load image
    # original_image = cv2.imread(image_path)
    original_image = image
    # cv2.imwrite("image_original.jpg",original_image)

    #Rotate image
    rotated_image = rotate_image(original_image)
    # cv2.imwrite("image_rotated.jpg",rotated_image)

    #Greyscale image
    greyscaled_image = cv2.cvtColor(rotated_image, cv2.COLOR_BGR2GRAY)
    # cv2.imwrite("image_greyscaled.jpg",greyscaled_image)

    #Threshold image
    thresh, thresholded_image = cv2.threshold(greyscaled_image,128,255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # cv2.imwrite("image_thresholded.jpg",thresholded_image)

    
    preprocessed_image = thresholded_image

    return preprocessed_image


def rotate_image(image):
    '''Use cv2 and pytesseract to rotate image right-way up
    '''

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Angle solution from
    # https://stackoverflow.com/questions/55119504/is-it-possible-to-check-orientation-of-an-image-before-passing-it-through-pytess
    angle = 360-int(re.search('(?<=Rotate: )\d+', pytesseract.image_to_osd(rgb_image)).group(0))

    #Rotate image using cv2 from
    # https://stackoverflow.com/questions/11764575/python-2-7-3-opencv-2-4-after-rotation-window-doesnt-fit-image

    #Get image height, width, center and set scale
    (h, w) = rgb_image.shape[:2]
    center = (w / 2, h / 2)
    scale = 1.0

    rotation_matrix = cv2.getRotationMatrix2D(center, angle, scale)

    #include if you want to prevent corners being cut off
    rad = np.deg2rad(angle)
    new_w,new_h = (abs(np.sin(rad)*h) + abs(np.cos(rad)*w),abs(np.sin(rad)*w) + abs(np.cos(rad)*h))

    #Find the translation that moves the result to the center of that region.
    (t_x,t_y) = ((new_w-w)/2,(new_h-h)/2)
    rotation_matrix[0,2] += t_x #third column of matrix holds translation, effects after rotation.
    rotation_matrix[1,2] += t_y

    rotated_image = cv2.warpAffine(rgb_image, rotation_matrix, dsize=(int(new_w),int(new_h)))

    return rotated_image


def ocr_preprocess(image):
    '''Preprocessing for an image for pytesseract after it is already loaded through cv2
    '''

    ret3, thresholded_image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # cv2.imwrite("thresholded.jpg",thresholded_image)
    ocr_image = cv2.cvtColor(thresholded_image, cv2.COLOR_BGR2RGB)
    # cv2.imwrite("greyscale.jpg",tesseract_image)

    return ocr_image
