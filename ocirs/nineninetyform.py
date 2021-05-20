import pathlib
import tempfile #For temporarily storing image files
import time # For timestamping saved files

from tqdm import tqdm #For displaying helpful progress bars
from pdf2image import convert_from_path #pdf to image handling
import fuzzysearch #Fuzzysearch for identifying form componenets via search_phrases.

#Class for individual nine ninety pages
from ocirs.nineninetypage import NineNinetyPage
#method for merging a list of similar dataframes
from ocirs.table_extraction.table_merge import merge_dataframes
#module for validating user inputs
import ocirs.validation_utils as validation_utils


class NineNinetyForm():

    '''A class for processing scanned IRS form 990s

    Forms consist of several parts and "schedules."

    Class works in concert with NineNinetyPage class to create a structure for analyzing the text
    of form 990s and extracting tabular data from certain form components.
    '''

    ###################################################################################
    # Class variable to define 990 form types that ocirs can handle
    ###################################################################################
    valid_form_types = {"990", "990PF"}

    ###################################################################################
    # A class variable that will define the parts of the irs form that the Class can process
    # Form component names adopted from naming conventions in [IRSx](http://www.irsx.info/)
    # New form components will be added as package maintainers improve flexibility of ocirs
    #################################################################################
    valid_form_components = {
        "990": {
            # "Frm990PrtVIISctnA": """Form 990 Part VII Compensation, Section A. Officers,
            #                         Directors, Highest Compensated Employees, etc.""",
            # "CntrctrCmpnstn": """Form 990 Part VII Compensation, Section B. Independant
            #                      Contractors""",
            "SkdIRcpntTbl": """Schedule I Part II, Grants and Other Assistance to Governments and
                               Organizations in the United States""",
            "SkdIGrntsOthrAsstTIndvInUS": """Schedule I Part III, Grants and Other Assistance to
                                             Individuals in the United States""",
            "SkdJRltdOrgOffcrTrstKyEmpl": """Schedule J Part II, Officers, Directors, Trustees, Key
                                             Employees, and Highest Compensated Employees""",
        },
        "990PF": {
            # "PFOffcrDrTrstKyEmpl": """Form 990PF Part VIII Compensation, 1. List all officers,
            #                           directors, etc. and their compensation""",
            # "PFCmpnstnHghstPdEmpl": """Form 990PF Part VIII Compensation, 2. Compensation of five
            #                            highest-paid employees""",
            # "PFCmpnstnOfHghstPdCntrct": """Form 990PF Part VIII Compensation, 3. Five highest-
            #                                paid independent contractors""",
            "PFGrntOrCntrApprvFrFt": """Form 990PF Part XV, Supplementary Information, Grant or
                                        Contribution Approved for Future Payment""",
            "PFGrntOrCntrbtnPdDrYr": """Form 990PF Part XV, Supplementary Information, Grant or
                                        Contribution Paid During Year""",
        },
    }

    ###################################################################################
    # A class variable of phrases that can be used to identify form components
    # These phrase are editable. If there is a new form component to search for, or a
    # different key phrase desired, simply edit this variable in your code like any other dict:
    # form_component_search_phrases['990']['Frm990PrtVIISctnA'].append("Directors, Trusties")
    ###################################################################################
    form_component_search_phrases = {
        "990": {
            "Frm990PrtVIISctnA": [
                                    "Section A. Officers, Directors, Trustees"
                                ],
            "CntrctrCmpnstn": [
                                    "Section B. Independent Contractors"
                            ],
            "SkdIRcpntTbl": [
                                "Part II Grants and Other Assistance to Domestic Organizations and Domestic Governments",
                                "Grants to Organizations and Governments in the U.S.",
                                "Grants and Other Assistance to Governments and Organizations in the United States. Complete if",
                                "Schedule I (Form 990) Part II, Line 1"
                            ],
            "SkdIGrntsOthrAsstTIndvInUS": [
                                            "Grants and Other Assistance to Domestic Individuals. Complete if",
                                            "Grants and Other Assistance to Individuals in the United States. Complete if"
                                        ],
            "SkdJRltdOrgOffcrTrstKyEmpl": [
                                            "For each Individual whose compensation must be reported in Schedule J",
                                            "Part II - Officers, Directors"
                                        ]
        },
        "990PF": {
            "PFOffcrDrTrstKyEmpl": [
                                        "List all officers, directors, trustees, foundation managers"
                                    ],
            "PFCmpnstnHghstPdEmpl": [
                                        "Compensation of five highest-paid employees"
                                    ],
            "PFCmpnstnOfHghstPdCntrct": [
                                            "Five highest-paid independent contractors for professional services"
                                        ],
            "PFGrntOrCntrApprvFrFt": [
                                        "Contributions Approved for Future Payment",
                                        "Grants and Contributions Paid During the Year or Approved for Future Payment",
                                        "Grants Approved for Future Payment"
                                    ],
            "PFGrntOrCntrbtnPdDrYr": [
                                        "Grants and Contributions Paid During the Year",
                                        "Grants Paid Calendar Year"
                                    ]
        }
    }

    def __init__(self, pdf_path, form_type, org_name=None, tax_period=None):


        self.pdf_file_path = pathlib.Path(pdf_path)
        self.form_type = "990PF" if form_type == "990-PF" else form_type #Standardize 990PF
        self.org_name = org_name
        self.tax_period = str(tax_period)
        self.form_components = {} #A dict for NineNinetyPage objs corresponding to form components
        self.pages = None
        ####
        # Need some method here that can tell us if the pdf is already text searchable
        # OCRmyPDF could do this, but that library is really for the command line
        ####

        ####
        # There should also be a method here for identifying whether the pdf already exists on IRS
        #  servers as an efiled xml document. But this is way in the future
        # https://github.com/jsfenfen/990-xml-reader#getting-an-object-id
        ####

    @property
    def pdf_file_path(self):
        '''Getter for self.pdf_file_path
        '''
        return self._pdf_file_path

    @pdf_file_path.setter
    def pdf_file_path(self, value):

        file_path = value #value will be a pathlib path object

        #########################################
        # Validate that path given leads to pdf
        #########################################
        if file_path.suffix != ".pdf":
            raise ValueError(f"'{value}' not a pdf file with a .pdf extension")

        #########################################
        # Validate that path given leads to a real file
        #########################################
        if not file_path.is_file():
            raise FileNotFoundError(f"File '{value}' does not exist at this path")

        self._pdf_file_path = value

    @property
    def form_type(self):
        '''Getter for self.form_type
        '''
        return self._form_type

    @form_type.setter
    def form_type(self, value):

        #########################################
        # Validate that form type given is one module knows how to handle
        #########################################
        form_type = str(value)
        if form_type not in NineNinetyForm.valid_form_types:
            raise ValueError(f"""NineNinetyForm can't do {form_type} forms yet.
                                Please input one of {NineNinetyForm.valid_form_types}""")

        self._form_type = form_type

    @property
    def org_name(self):
        '''Getter for self.org_name
        '''
        return self._org_name

    @org_name.setter
    def org_name(self, value):
        self._org_name = value

    def extract_pages(self, save_path=None, save_type=None):
        '''OCR's the entire form pdf

        Stores the resulting text data within in a list of NineNinetyPage objects.

        This is a slow function. It should only be called once for an instance of NineNinetyForm.
        Page data can then be requested either through self.pages (set at the end of this function)
        or by loading pre-ocr'ed page data via `self.load_pages()`.

        Goal of this function is to set self.pages = pages

        :param save_path: path to a directory
        :type save_path: string
        :param save_type: file extension, either "csv" or "pickle"
        :type save_type: string

        :returns: list of NineNinetyPage objects
        :rtype: list

        '''
        print(self.pdf_file_path)

        ###############################
        # Before ocr'ing pdf, validate the save inputs if the user provides them
        ###############################
        if save_path:
            validation_utils.validate_extract_pages_save_path(save_path)
            if save_type:
                validation_utils.validate_extract_pages_save_type(save_type)

        #All NineNinetyPage objects will be appended to this list
        pages = []

        #Temp directory used to easily manage memory and storage requirements of loading pdf images
        with tempfile.TemporaryDirectory() as temp_path:

            #Convert pdf to images stored in temporary directory. Return temporary paths
            print("Converting pdf to images. Large pdfs will take a while ...")
            page_image_paths = convert_from_path(self.pdf_file_path, dpi=300, grayscale=True,
                                                paths_only=True, output_folder=temp_path)
            print("... Done!")

            # Iterate each image (page), return instance of NineNinetyPage with data attached
            print("OCR-ing pdf pages. This may take a while ...")
            for index,path in enumerate(tqdm(page_image_paths)):
                page = NineNinetyPage(image_path=path, data_path=None, parent_nineninetyform=self,
                                        index=index)
                pages.append(page)
            print("... Done!")


        ######################################################
        # If the user provides save_path when calling extract_pages(), save the dataframes in the
        # directory provided, in the format requested
        #####################################################
        if save_path:
            print("Save path provided ...")
            print(f"Saving page data to {save_path}")
            print(f"Saving as {save_type}")

            time_stamp = int(time.time())

            if save_type == "csv":
                for page in pages:
                    full_page_save_path = pathlib.PurePath(save_path, 
                                                            f"{time_stamp}_{self.org_name}_{self.form_type}_{self.tax_period}_{page.index}.{save_type}")
                    page.ocr_dataframe.to_csv(full_page_save_path, index=False)
            elif save_type == "pickle":
                for page in pages:
                    full_page_save_path = pathlib.PurePath(save_path, 
                                                            f"{time_stamp}_{self.org_name}_{self.form_type}_{self.tax_period}_{page.index}")
                    page.ocr_dataframe.to_pickle(full_page_save_path)

        else:
            print("No save path provided for extracted pages")

        self.pages = pages


        return pages


    def load_pages(self, data_path_list, page_index_list):
        '''Use a series of pre-ocr'ed data files and corresponding page indices to populate list of
        NineNinetyPage objects.

        Data files must be derrived from
        `pytesseract.image_to_data(tesseract_image, output_type=pytesseract.Output.DATAFRAME)` and
        saved using pandas' `df.to_csv()` or `df.to_pickle()` dataframe methods. This mirrors the
        process used in `extract_pages()`

        `page_index_list` is a list of integers, whose value is the page index of the original pdf.
        To determine what "page" a `data_path_list` item represents, view corresponding value at
        the same index in `page_index_list`.

        For example:
        For the following inputs `[data_path_0, data_path_1, data_path_2], [0, 33, 34]`,
        `data_path_1` represents page data for the 33rd page (counting from 0) of the pdf.

        If page data was originally extracted and saved using `extract_pages()`, the page index
        will be saved into the name of the data path. To quickly extract these indicies from a
        list of pickle paths:
        ```
        data_paths = glob.glob('temp_data/**')
        page_index_list = list(map(lambda x: x.split("_")[-1], data_paths))
        ```

        :param data_path_list: List of paths to ocr data files
        :type data_path_list: list
        :param page_index_list: List of data paths' corresponding pdf page indices
        :type page_index_list: list

        :returns: list of NineNinetyPage objects
        :rtype: list
        '''

        ############################
        # Validate that the user has provided a data_path_list and a page_index_list of the same
        # length
        ############################
        validation_utils.validate_load_pages_list_length(data_path_list, page_index_list)

        ############################
        # Iterate through list of data paths, create NineNinetyPage objects and append to pages
        # list
        ############################

        #Create pages list. Will be filled with NineNinetyPage objects
        pages = []

        with tempfile.TemporaryDirectory() as temp_path:

            #Convert pdf to images stored in temporary directory. Return temporary paths
            print("Converting pdf to images. Large pdfs will take a while ...")
            page_image_paths = convert_from_path(self.pdf_file_path, dpi=300, grayscale=True,
                                                paths_only=True, output_folder=temp_path)
            print("... Done!")

            print("Loading pdf images and data paths into NineNinetyPage objects ... ")
            for index, data_path in enumerate(tqdm(data_path_list)):
                page = NineNinetyPage(image_path=page_image_paths[int(page_index_list[index])],
                                        data_path=data_path, parent_nineninetyform=self,
                                        index=page_index_list[index])
                pages.append(page)
            print("... Done!")

        self.pages = pages

        return pages


    def search_form(self, form_component):
        '''Searches entire NineNinetyForm for user-identified form component

        User can only request form components listed in `NineNinetyForm.valid_form_components`

        To add additional searchable form components, edit both
        `NineNinetyForm.valid_form_components` and `NineNinetyForm.form_component_search_phrases`
        prior to calling this function.

        Function will return list of pages AND populate self.form_components with key/value pairs
        if matching pages are identified.

        :param form_component: irsx-style string name of form component
        :type form_component: string

        :returns: List of NineNinetyPage object determined to be part of requested form component
        :rtype: list
        '''

        #Create list to store identified form component pages
        pages = []

        # Validate that submitted form component is handlable
        validation_utils.validate_form_component(form_component, 
                                                NineNinetyForm.valid_form_components[self.form_type].keys())
        # Confirm NineNinetyForm object has already processed pages.
        # Required for search_form() function
        validation_utils.validate_page_attribute(self)

        #Grab search phrases
        search_phrases = NineNinetyForm.form_component_search_phrases[self.form_type][form_component]
        #Iterate through NineNinetyForm instances pages, search for matches
        for page in self.pages:
            page_text = page.ocr_dataframe_to_text() #Turn ocr data into single string of page text
            is_phrase_detected = NineNinetyForm.phrase_match(search_phrases, page_text)
            if is_phrase_detected:
                pages.append(page)

        self.form_components[form_component] = pages

        return pages

    def extract_component_tables(self, form_component, merge=False, use_cascadetabnet=False, 
        table_type="bordered", extraction_method="custom"):
        '''Extracts tabular data for a specific form component

        Combines `search_form()` (if not previously requested) and
        `NineNinetyPage().extract_tables()` to collect data from desired form pages.

        If `merge=True`, then `merge_dataframes()` will be called on the list of returned
        dataframes, an attempt to fuzzymerge the returned tabular data into a single dataframe.

        If no tables are extracted, it is possible ocirs could not extract tables from the desired
        pages. It's also possible that `search_form()` did not identify any pages for that form
        component.

        :param form_component: irsx-style string name of form component
        :type form_component: string
        :param merge: True/False value of whether to ask ocirs to attempt to combine extracted
        tables into one. Default is False
        :type merge: bool
        :param use_cascadetabnet: True/False value of whether to use CascadeTabNet table detection
        model. Requires CUDA-enabled GPU
        :type use_cascadetabnet: bool
        :param table_type: What type of tables will ocris be processing. Either "bordered" or
        "borderless". "detect" is also available when `use_cascadetabnet=True`
        :type table_type: string
        :param extraction_method: Table extraction method to use. "custom" is only current option.
        :type extraction_method: string

        :returns: List of NineNinetyPage object determined to be part of requested form component
        :rtype: list
        '''

        #####################################
        # First, check whether NineNinetyForm instance has pages for requested form component
        #####################################
        if form_component not in self.form_components: #search_form() has not been called. Do now
            component_pages = self.search_form(form_component)
        else:
            component_pages = self.form_components[form_component]

        #Warn users that there are no pages to extract tables from
        if not component_pages:
            print("Warning! No component pages found. No tables to extract")

        ###################################
        # Next, iterate through component page list and extract tables
        #####################################
        component_table_dataframes = []
        print(f"Extracting tables from {form_component} pages. This may take a while ...")
        for page in tqdm(component_pages):
            #Pull dataframe list from page
            dataframe_list = page.extract_tables(use_cascadetabnet=use_cascadetabnet,
                                                table_type=table_type,
                                                extraction_method=extraction_method)
            component_table_dataframes = component_table_dataframes + dataframe_list
        # print("... Done!")

        if merge:
            component_table_dataframes = merge_dataframes(component_table_dataframes)

        return component_table_dataframes

    @staticmethod
    def phrase_match(phrase_list, page_text, max_l_dist=4):
        '''Fuzzysearches `page_text` for phrases pased in `phrase_list`.

        String matching performed using the [fuzzysearch](https://github.com/taleinat/fuzzysearch)
        Python package.

        :param phrase_list: phrase list corresponding to certain form component
        :type phrase_list: list
        :param page_text: page text
        :type page_text: string
        :param max_l_dist: maximum levenshtein distance for fuzzysearch, default 4
        :type max_l_dist: integer

        :returns: bool depending if a phrase was matched within certain levenshtein distance
        :rtype: bool
        '''

        detected_phrase = False

        ######################################################
        #Iterate through the phrase list and detect matches
        #####################################################
        ##### Fuzzysearch: https://github.com/taleinat/fuzzysearch
        for phrase in phrase_list:
            #Search page text for a phrase within 2 character changes (levenstein distance)
            if len(fuzzysearch.find_near_matches(phrase.lower(), page_text.lower(),
                                                max_l_dist=max_l_dist)
                ):
                detected_phrase = True
                break

        return detected_phrase
