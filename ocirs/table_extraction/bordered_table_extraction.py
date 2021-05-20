import numpy as np
import pandas as pd
import cv2
import pytesseract


def get_bordered_table(image, ocr_dataframe=None):
    '''
    NOTE: Still need to figure out how to leverage pre-computed ocr_dataframe

    '''

    #inverting the image
    img_bin = 255-image
    # cv2.imwrite('cv_inverted.jpg',img_bin)

    # Length(width) of kernel as 100th of total width
    kernel_len = np.array(image).shape[1]//100
    

    # Defining a vertical kernel to detect all vertical lines of image
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))

    # Defining a horizontal kernel to detect all horizontal lines of image
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))


    # A kernel of 2x2
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))


    #Use vertical kernel to detect and save the vertical lines in a jpg
    image_1 = cv2.erode(img_bin, ver_kernel, iterations=3)
    vertical_lines = cv2.dilate(image_1, ver_kernel, iterations=3)
    # cv2.imwrite("vertical.jpg",vertical_lines)

    #Use horizontal kernel to detect and save the horizontal lines in a jpg
    image_2 = cv2.erode(img_bin, hor_kernel, iterations=3)
    horizontal_lines = cv2.dilate(image_2, hor_kernel, iterations=3)

    #cv2.line(image, start_point, end_point, color, thickness)
    # horizontal_lines = cv2.line(horizontal_lines,(min_x,min_y), (min_x,max_y),(0,255,0),20)
    # horizontal_lines = cv2.line(horizontal_lines,(max_x,min_y), (max_x,max_y),(0,255,0),20)
    # horizontal_lines = horizontal_lines[y:y+h, x:x+w]

    # cv2.imwrite("horizontal.jpg",horizontal_lines)

    # Combine horizontal and vertical lines in a new third image, with both having same weight.
    img_vh = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)


    #Identify boundaries of table 
     # cv2.line(img,(x1,y1),(x2,y2),(0,255,0),2)
    min_y = horizontal_lines.shape[0]
    max_y = 0
    min_x = img_vh.shape[1]
    max_x = 0
    for y_index,pixel_row in enumerate(horizontal_lines):
        for x_index, pixel in enumerate(pixel_row):
            if pixel == 255:

                if y_index < min_y: 
                    min_y = y_index
                if y_index > max_y:
                    max_y = y_index
                if x_index < min_x:
                    min_x = x_index
                if x_index > max_x:
                    max_x = x_index

    for y_index,pixel_row in enumerate(vertical_lines):
        for x_index, pixel in enumerate(pixel_row):
            if pixel == 255:

                if y_index < min_y: 
                    min_y = y_index
                if y_index > max_y:
                    max_y = y_index
                if x_index < min_x:
                    min_x = x_index
                if x_index > max_x:
                    max_x = x_index

    # #Crop image to the edges of the table
    # img_vh = img_vh[min_y:max_y, min_x:max_x]
    # #Crop original table image 
    # img_orig_cropped = img[min_y:max_y, min_x:max_x]

    # #Add bounding lines to improve table detection when table is missing border lines on either side
    img_vh = cv2.line(img_vh,(min_x,min_y), (min_x,max_y),255,5)
    img_vh = cv2.line(img_vh,(max_x,min_y), (max_x,max_y),255,5)



    #Eroding and thesholding the image
    img_vh = cv2.erode(~img_vh, kernel, iterations=2)
    thresh, img_vh = cv2.threshold(img_vh,128,255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)



    # cv2.imwrite("combined.jpg", img_vh)


    bitxor = cv2.bitwise_xor(image,img_vh)
    bitnot = cv2.bitwise_not(bitxor)

    # Detect contours for following box detection
    contours, hierarchy = cv2.findContours(img_vh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Sort all the contours by top to bottom.
    contours, boundingBoxes = sort_contours(contours, method="top-to-bottom")
    
    #Creating a list of heights for all detected boxes
    heights = [boundingBoxes[i][3] for i in range(len(boundingBoxes))]#Get mean of heights
    mean = np.mean(heights)
    
    #Create list box to store all boxes in  
    box = []
    # Get position (x,y), width and height for every contour and show the contour on image
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)    
        if (w<1000 and h<500): #WE MAY NEED TO ADJUST THESE VALUES TO BETTER DETECT CELLS. Values are for the max height and width of a certain cells. Avoids detecting a large box that is not really a cell
            image = cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),2)
            box.append([x,y,w,h])
       

    #Creating two lists to define row and column in which cell is located
    row=[]
    column=[]
    j=0
    #Sorting the boxes to their respective row and column
    for i in range(len(box)):    
        if(i==0):
            column.append(box[i])
            previous=box[i]    
        else:
            if(box[i][1]<=previous[1]+mean/2):
                column.append(box[i])
                previous=box[i]            
                
                if(i==len(box)-1):
                    row.append(column)        
            else:
                row.append(column)
                column=[]
                previous = box[i]
                column.append(box[i])

    #calculating maximum number of cellscountcol = 0
    for i in range(len(row)):
        countcol = len(row[i])
        if countcol > countcol:
            countcol = countcol
    
    #Retrieving the center of each column
    center = [int(row[i][j][0]+row[i][j][2]/2) for j in range(len(row[i])) if row[0]]
    
    center = np.array(center)
    center.sort()

    #Regarding the distance to the columns center, the boxes are arranged in respective order
    finalboxes = []
    for i in range(len(row)):
        lis=[]
        for k in range(countcol):
            lis.append([])
        for j in range(len(row[i])):
            diff = abs(center-(row[i][j][0]+row[i][j][2]/4))
            minimum = min(diff)
            indexing = list(diff).index(minimum)
            lis[indexing].append(row[i][j])
        finalboxes.append(lis)


    #from every single image-based cell/box the strings are extracted via pytesseract and stored in a list
    # print(finalboxes)
    #Need to combine final boxes with ocr_dataframe
    # Think what you have to do is iterate through finalboxes and leverage the [y,x,w,h] value of each "box".
    # Compare the values to whats available to ocr_dataframe


    outer=[]
    for i in range(len(finalboxes)):
        for j in range(len(finalboxes[i])):
            inner=''
            # print(finalboxes[i][j])
            if(len(finalboxes[i][j])==0):
                outer.append(' ')        
            else:
                for k in range(len(finalboxes[i][j])):
                    y,x,w,h = finalboxes[i][j][k][0],finalboxes[i][j][k][1], finalboxes[i][j][k][2],finalboxes[i][j][k][3]

                    #Table cell by table cell pre-processing before pytesseract
                    finalimg = bitnot[x:x+h, y:y+w] #Crop the big image to just the small box denoted by one of the final boxes
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
                    border = cv2.copyMakeBorder(finalimg,2,2,2,2,   cv2.BORDER_CONSTANT,value=[255,255])
                    resizing = cv2.resize(border, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                    dilation = cv2.dilate(resizing, kernel,iterations=1)
                    erosion = cv2.erode(dilation, kernel,iterations=1)

                    
                    out = pytesseract.image_to_string(erosion)
                    if(len(out)==0):
                        out = pytesseract.image_to_string(erosion, config='--psm 3')
                    inner = inner +" "+ out            
                outer.append(inner.strip())

    #Creating a dataframe of the generated OCR list
    arr = np.array(outer)
    dataframe = pd.DataFrame(arr.reshape(len(row), countcol))
    # dataframe.to_csv("processed_csv.csv", index=False)

    return dataframe



def sort_contours(cnts, method="left-to-right"):
    
    # initialize the reverse flag and sort index
    reverse = False
    i = 0    
    
    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True    
    
    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1    
    
    # construct the list of bounding boxes and sort them from top to bottom
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes), key=lambda b:b[1][i], reverse=reverse))

    return (cnts, boundingBoxes)