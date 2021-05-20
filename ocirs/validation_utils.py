import pathlib

###############################
# For NineNinetyForm().extract_pages() method
###############################
def validate_extract_pages_save_path(save_path):
    if not pathlib.Path(save_path).is_dir():
        raise Exception(f"""Directory not found at {save_path} 
                        Please provide a valid directory to save_path""")

def validate_extract_pages_save_type(save_type):
    if save_type not in ("csv","pickle"):
        raise ValueError(f"""Please provide a valid extension to save_type: 'csv' or 'pickle'. 
                            Current save_type argument {save_type}""")

###############################
# For NineNinetyForm().load_pages() method
###############################
def validate_load_pages_list_length(data_paths_list, page_index_list):
    if len(data_paths_list) != len(page_index_list):
        raise Exception("`data_paths_list` and `page_index_list` must be of the same length")

###############################
# For NineNinetyPage().extract_tables() method
###############################
def validate_extract_tables_settings(use_cascadetabnet, table_type, extraction_method):

    if not isinstance(use_cascadetabnet, bool):
        raise TypeError(f"`use_cascadetabnet` must be boolean value. Recieved {use_cascadetabnet}")

    if table_type not in ("bordered", "borderless", "detect"):
        raise ValueError(f"""table_type must be set to one of 'bordered', 'borderless' or 'detect'. 
                        Recieved '{table_type}'""")

    #If not using CascadeTabNet and no table type specified
    if not use_cascadetabnet and table_type == "detect": 
        raise Exception(f"""`table_type` cannot be '{table_type}' if `use_cascadetabnet=False`, 
                        please specify either 'bordered' or 'borderless'.""")

#################################
# General validators
#################################
def validate_form_component(form_component, valid_form_components):
    if form_component not in valid_form_components:
        raise Exception(f"""Form component provided, {form_component}, not currently supported by
                         NineNinetyForm. To view available form components: 
                         `NineNinetyForm.valid_form_components`""")

def validate_page_attribute(nineninetyformobj):
    if not hasattr(nineninetyformobj, "pages"):
        raise AttributeError("""'NineNinetyForm' instance has no attribute 'pages'. Try calling
                             `load_pages()` or `extract_pages()` on object instance to correct 
                             this error.""")
