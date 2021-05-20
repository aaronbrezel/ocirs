from ocirs import NineNinetyForm
from ocirs import NineNinetyPage

import glob

from ocirs.table_extraction.table_merge import merge_dataframes, clean_dataframe


import cv2
import pandas as pd
import pathlib

import time

#################################
# Test instantiation of NineNinetyForm object
#################################
# pdf_obj = NineNinetyForm("Charles Koch Institute_2013.pdf", "990", "charles_koch_institute", 2013)

#################################
# Test adding of current processable 990 sections
#################################
# print(NineNinetyForm.valid_form_components)
# NineNinetyForm.valid_form_components['990']["irsxComponent"] = Schedule Pi Part Rho, Accounting of baked goods delivered'
# print(NineNinetyForm.valid_form_components)
# NineNinetyForm.form_component_search_phrases['990']['irsxComponent'] = ["Accounting of baked goods delivered", "Pies sent, pies recieved"]



#################################
# Test extraction and save of NineNinetyForm pages
#################################
# pdf_obj.extract_pages(save_path="temp_data", save_type="pickle")


#################################
# Test loading data into NineNinetyPage object instead of ocr
#################################
# page_obj = NineNinetyPage("Charles Koch Institute_2013_25.jpg", data_path="temp_data/1620360597_charles_koch_institute_990_2013_25", index=25)
# print(page_obj.ocr_dataframe)


###################################
# Test loading list of data paths into NineNinetyForm object
###################################
# pdf_obj = NineNinetyForm("Charles Koch Institute_2013.pdf", "990", "charles_koch_institute", 2013)
# data_path_list = glob.glob('temp_data/**')
# page_index_list = list(map(lambda x: x.split("_")[-1], data_path_list))
# pages = pdf_obj.load_pages(data_path_list, page_index_list)
# print(pages[-1].ocr_dataframe)
# print(pages[-1].index)
# cv2.imwrite("test.png", pages[-1].image)


###################################
# Test searching for specific form component in a NineNinetyForm object
###################################
# pdf_obj = NineNinetyForm("Charles Koch Institute_2013.pdf", "990", "charles_koch_institute", 2013)
# data_path_list = glob.glob('temp_data/**')
# page_index_list = list(map(lambda x: x.split("_")[-1], data_path_list))
# pdf_obj.load_pages(data_path_list, page_index_list)
# returned_pages = pdf_obj.search_form("SkdIGrntsOthrAsstTIndvInUS")
# print(pdf_obj.form_components)


###################################
# Test extracting table from specific NineNinetyPage object using custom extraction
###################################
# page_obj = NineNinetyPage("Charles Koch Institute_2013_25.jpg", index=None)
# print(page_obj.ocr_dataframe)
# results = page_obj.extract_tables(use_cascadetabnet=True,table_type="detect",extraction_method="custom")
# print(results[0].head())
# page_obj = NineNinetyPage("Sarah Scaife Foundation_2014_38.jpg")
# page_obj.extract_tables(use_cascadetabnet=False,table_type="borderless",extraction_method="custom")

###################################
# Test full table extraction of specific NineNinety form component starting from object instance
###################################
# pdf_obj = NineNinetyForm("short_pdf_sch_i.pdf", "990", "charles_koch_institute", 2013)
# pdf_obj.extract_pages()
# print(pdf_obj.pages)
# df = pdf_obj.extract_component_tables("SkdIRcpntTbl", merge=True, use_cascadetabnet=False, table_type="bordered", extraction_method="custom")
# print(df)

###################################
# Test full table extraction of specific NineNinety form component starting from loaded pages
###################################
# pdf_obj = NineNinetyForm("Charles Koch Institute_2013.pdf", "990", "charles_koch_institute", 2013)
# data_path_list = glob.glob('temp_data/**')
# page_index_list = list(map(lambda x: x.split("_")[-1], data_path_list))
# pdf_obj.load_pages(data_path_list, page_index_list)
# pdf_obj.search_form("SkdIGrntsOthrAsstTIndvInUS")
# pdf_obj.extract_component_tables("SkdIRcpntTbl", merge=True, use_cascadetabnet=False, table_type="bordered")

####################################
# Test merging of component dataframes
####################################
# data_paths = glob.glob('**.csv')
# dataframe_list = []

# for data_path in data_paths:
#     dataframe = pd.read_csv(data_path)
#     dataframe_list.append(dataframe)


# merged_df = merge_dataframes(dataframe_list)

# merged_df.to_csv("merged_df.csv", index=False)

#####################################
# Code to test speeding up table extraction process
####################################
start_time = time.time()
#Borderless table processing time
page_obj = NineNinetyPage("test_files/Sarah Scaife Foundation_2015_36_0_borderless.jpg", index=None)
page_obj.extract_tables(use_cascadetabnet=False,table_type="borderless",extraction_method="custom")
print(page_obj.tables)
# img = cv2.imread("Sarah Scaife Foundation_2015_36_0_borderless.jpg")
# print(img.shape)
# Bordered table processing
# page_obj = NineNinetyPage("test_files/Charles Koch Institute_2013_25_0_bordered.jpg", index=None)
# page_obj.ocr_dataframe.to_csv("ocr_dataframe.csv", index=False)
# dataframes = page_obj.extract_tables(use_cascadetabnet=False,table_type="bordered",extraction_method="custom")
# print(dataframes[0])
# dataframes[0].to_csv("test_files/test_OI.csv", index=False)

end_time = time.time()

print(f"Processing time: {end_time-start_time}")