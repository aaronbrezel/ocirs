import cv2

from ocirs.image_utils import table_preprocess
from ocirs.table_extraction.bordered_table_extraction_TDS import get_bordered_table_TDS
from ocirs.table_extraction.bordered_table_extraction_OI import get_bordered_table_OI
from ocirs.table_extraction.borderless_table_extraction import get_borderless_table






#NEED some way to remove these imports if some flag is set
try:
    from ocirs.table_detection.cascadetabnet import define_model, cascadetabnet_crop_table
    exists_cascadetabnet = True
except:
    print("Error importing CascadeTabNet. Table detection will be unavailable")
    exists_cascadetabnet = False


def extract_tables(image, ocr_dataframe=None, use_cascadetabnet=False, table_type="bordered", extraction_method="custom"):
    '''
    The primary function for extracting tables from an image. All other functions in this file all called through this master function.

    It takes a single image and retuns a pandas dataframe any tabular data detected.

    Several additional options are available
    * ocr_datafame: The option to upload a pre-computed dataframe of ocr data calculated using the pytesseract.image_to_data() method with output_type=pytesseract.Output.DATAFRAME
    * use_cascadetabnet: A True/False flag to let the user specify whether they want to use CascadeTabNet to detect tables and crop the original image down to just that image 
    * table_type: Either "bordered" or "borderless" tells the function what kind of table extraction method to use.
    * extraction_method: Either "custom" or "pdfplumber". Right now only custom will work
    '''

    ###########################
    # First, load and preprocess image
    ###########################
    preprocessed_image = table_preprocess(image)

    ###########################
    # If use_cascadetabnet=True, run CascadeTabNet process to detect the table(s) and crop the image down
    # Returns a list of tuples. Each tuple represnets a detected table and consists of two components.
    # First a numpy-array representation of the cropped table image. Second an assertion of whether the table is bordered or borderless
    ###########################
    if use_cascadetabnet: 
      
        #Throw exception if cascadetabnet is unavailable
        if not exists_cascadetabnet:
            raise Exception("Error establishing CascadeTabNet process. Make sure all relevant dependances are installed, or set `use_cascadetabnet=False`.")
       

        #First define the model that will be used to detect tables in the image
        model = define_model()
        #Then run wrapper function that detects, labels and crops tables from image
        table_list = cascadetabnet_crop_table(model, cv2.cvtColor(preprocessed_image, cv2.COLOR_GRAY2RGB)) #NOTE:Trouble running mmdet on 1-channel greyscale image, making cv2.COLOR_GRAY2RGB necessary
        
        # IMPORTANT
        # Wipe the original ocr_dataframe. Since we're croping the image, we'll need new text data 
        # That new text data will be added via `get_text_boxes()``
        ocr_dataframe = None

        #Iterate through list of returned tuples. Set image back to greyscale. Set table type if user requests
        for index,table_tuple in enumerate(table_list):
            table_list[index] = (cv2.cvtColor(table_list[index][0], cv2.COLOR_RGB2GRAY), table_type if table_type != "detect" else table_list[index][1])
            

    ###################
    # Else, just power ahead with the original preprocessed image
    # But standardize the output so we can move forward with the same data structure
    ###################
    else:
        table_list = [(preprocessed_image,table_type)]


    #############################
    # Finally, iterate through each image (cropped or uncropped) and enter the 
    # table extraction process for the specified table type 
    ############################
    table_dataframes = []
    for table_tuple in table_list:
        if table_tuple[1] == "bordered":
            # dataframe = get_bordered_table_TDS(table_tuple[0], ocr_dataframe)
            dataframe = get_bordered_table_OI(table_tuple[0], ocr_dataframe)
            print(dataframe)
            cv2.imwrite("Test.jpg", table_tuple[0])
        elif table_tuple[1] == "borderless":
            dataframe = get_borderless_table(table_tuple[0], ocr_dataframe)

        table_dataframes.append(dataframe)

    
    ##########################
    # Our returned data structure will be a list of pandas dataframes
    # Each dataframe corresponds to one table detected on the page
    ###########################


    return table_dataframes

