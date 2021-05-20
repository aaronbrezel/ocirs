import pathlib

from ocirs.table_extraction.table_extraction import extract_tables
from ocirs.image_utils import ocr_preprocess
from ocirs.validation_utils import validate_extract_tables_settings


#Pytesseract w/ configuration
#psm 1 lets pytesseract to read rotated text. 990s often have pages with different orientations
import pytesseract
PYTESSERACT_CUSTOM_CONFIG = "--oem 3 --psm 1"

import cv2
import pandas as pd

class NineNinetyPage():
    '''A class for processing scanned IRS form 990 pages

    Each form page is self contained, consisting of an image of the page (loaded using cv2 on
    initialization) and a dataframe of ocr data (created on initialization). A page may be linked
    to a parent form 990 and may be given a page index.

    If loading a data path, data files must be derrived from
    `pytesseract.image_to_data(tesseract_image, output_type=pytesseract.Output.DATAFRAME)` and
    saved using pandas' `df.to_csv()` or `df.to_pickle()` dataframe methods. This mirrors the
    process used in `ocr()`.
    '''

    def __init__(self, image_path, data_path=None, parent_nineninetyform=None, index=None):

        self.image_path = pathlib.Path(image_path)
        self.image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        self.data_path = data_path
        self.parent_nineninetyform = parent_nineninetyform
        self.index = int(index) if index else index #Converts input to int, else keeps as Nonetype
        self.ocr_dataframe = self.ocr() if image_path and not data_path else self.load_ocr_dataframe()
        self.tables = None

    @property
    def image_path(self):
        '''Getter for self.image_path
        '''
        return self._image_path
    @image_path.setter
    def image_path(self, value):
        if not value.is_file():
            raise FileNotFoundError(f"Image file does not exist at {value}")

        self._image_path = value

    @property
    def data_path(self):
        '''Getter for self.data_path
        '''
        return self._data_path
    @data_path.setter
    def data_path(self, value):

        ###########################
        # if data_path=None, validate and move on
        ###########################
        if not value:
            self._data_path = value

        #########################################
        # Else, make sure the file exists at this data path
        #########################################
        else:
            #NOTE: is it kosher to change the type of an initialization variable during validation?
            data_path = pathlib.Path(value)
            if not data_path.is_file():
                raise FileNotFoundError(f"Data file does not exist at {value}")

            self._data_path = data_path

    @property
    def parent_nineninetyform(self):
        '''Getter for self.parent_nineninetyform
        '''
        return self._data_path

    @parent_nineninetyform.setter
    def parent_nineninetyform(self, value):

        #########################
        # TODO: Fix isinstance type check to make sure value is an instance of NineNinetyForm
        # running into circular import error
        ########################

        ###########################
        # if parent_nineninetyform=None, validate and move on
        ###########################
        if not value:
            self._parent_nineninetyform = value

        #########################################
        # Else, make sure input is of type NineNinetyForm
        #########################################
        else:
            self._parent_nineninetyform = value
            # if isinstance(value, NineNinetyForm):
            #     self._parent_nineninetyform = value
            # else:
            #     raise TypeError(f"{value} is not NineNinetyForm instance")

    @property
    def index(self):
        '''Getter for self.index
        '''
        return self._index

    @index.setter
    def index(self, value):

        ###########################
        # Make sure input value is type int or None
        ###########################
        if isinstance(value, int) or value is None:
            self._index = value
        else:
            raise TypeError(f"index must be type int. Recieved: {value} of type {type(value)}")




    def ocr(self):

        '''Use pytesseract to extract ocr data from image

        Data extracted as `pytesseract.Output.DATAFRAME`.

        Method called automatically on class object initialization. Don't call this on your own.

        :returns: pytesseract.Output.DATAFRAME of ocr data
        :rtype: dataframe
        '''
        #########################################
        # Preprocess image in prep for pytesseract ocr
        ########################################
        tesseract_image = ocr_preprocess(self.image)

        ########################################
        # OCR image using pytesseract
        ########################################
        ocr_dataframe = pytesseract.image_to_data(
            tesseract_image,
            output_type=pytesseract.Output.DATAFRAME,
            config=PYTESSERACT_CUSTOM_CONFIG
        )

        return ocr_dataframe

    def load_ocr_dataframe(self):
        '''Load ocr data into NineNinetyPage object

        Method called automatically on class object initialization. Don't call this on your own.

        :returns: pytesseract.Output.DATAFRAME of ocr data
        :rtype: dataframe

        '''

        if self.data_path.suffix == ".csv":
            ocr_dataframe = pd.read_csv(self.data_path)
        else: #WIll have to reserve this clause for pickles since there is no extension to utilize
            ocr_dataframe = pd.read_pickle(self.data_path)

        return ocr_dataframe

    def ocr_dataframe_to_text(self):
        '''Converts ocr_dataframe to single text string

        Useful for performing text search on page.

        :returns: ocr'ed text as string
        :rtype: string
        '''
        ###############################
        #First, remove text with confidence level of -1
        #############################
        trunc_dataframe = self.ocr_dataframe[~(self.ocr_dataframe["conf"]==-1)]

        ###############################
        # Next, iterate through text values of dataframe and stitch together full page text
        ###############################
        page_text = ""
        for value in trunc_dataframe['text']:
            value = str(value)

            if value.isspace(): #Check if text is just empty space
                #If it is, simply append value to end of page_text string
                page_text = page_text + value
            else:
                page_text = page_text + value + " "

        # Strip leading and trailing spaces from page text
        page_text = page_text.strip()

        return page_text

    def extract_tables(self, use_cascadetabnet=False, table_type="bordered",
        extraction_method='custom'):
        '''Extract tabular data from NineNinetyPage object

        Returns list of dataframes, each representing a table detected on the page. Also sets
        self.tables to that value.

        This is a wrapper function for the `extract_tables()` method located in
        table_extraction/table_extraction.py.

        In addition to an image and a ocr dataframe, table_extraction.extract_table() takes three
        setting inputs.

        *use_cascadetabnet: a True/False flag indicating whether the user wants to detect a table
        and table_type using CasecadeTabNet (currently requires a CUDA-enabled gpu)
        *table_type: None, "bordered" or "borderless" indicates what type of table is contained in
        the NineNinetyPage object. If set to "bordered" or "borderless" the process will assume all
        tables on the page are of that type.
        *extraction_method: Indicates how to extracttabular data. "custom" table extraction process
        derived from open-intelligence, CascadeTabNet and Towards Data Science.

        If use_cascadetabnet = True and table_type=None, then the type of table will be
        automatically detected by CascadeTabnet and applied.
        If use_cascadetabnet = False, then the user must specify the type of table to extract.

        This method passes these setting variable directly to the table_extraction function.

        :param use_cascadetabnet: True/False value of whether to use CascadeTabNet table detection
        model. Requires CUDA-enabled GPU
        :type use_cascadetabnet: bool
        :param table_type: What type of tables will ocris be processing. Either "bordered" or
        "borderless". "detect" is also available when `use_cascadetabnet=True`
        :type table_type: string
        :param extraction_method: Table extraction method to use. "custom" is only current option.
        :type extraction_method: string

        :returns: list of dataframes containing tabular data found in NineNinetyPage object image
        :rtype: list
        '''

        #Retaining extraction_method="custom" validation here since it's intended to be removed
        # eventually
        if extraction_method != "custom":
            raise ValueError(f'extraction_method must be "custom". Recieved "{extraction_method}"')

        ############################
        # Validate extract table settings
        ############################
        validate_extract_tables_settings(use_cascadetabnet, table_type, extraction_method)

        ##############################
        # Extract tables
        #############################
        result = extract_tables(self.image, self.ocr_dataframe, use_cascadetabnet, table_type,
                                extraction_method)

        self.tables = result

        return result
