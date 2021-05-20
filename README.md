# ocirs

## What is ocirs?

ocris is a Python package for extracting text and tabular data from IRS form 990s.

It uses a custom configuration of [pytesseract](https://github.com/madmaze/pytesseract) to extract text data. To collect tabular data, it uses a combination of [open-cv](https://opencv.org/), [CascadeTabNet](https://github.com/DevashishPrasad/CascadeTabNet) and methods described in [Open-Intelligence](https://github.com/nazarimilad/open-intelligence-backend) and [Towards Data Science](https://towardsdatascience.com/a-table-detection-cell-recognition-and-text-extraction-algorithm-to-convert-tables-to-excel-files-902edcf289ec).

**This package is a work in progress. The tabular extraction process is imperfect, but will improve and encompass more form components in future iterations.**

## What are form 990s?

Form 990s are how most nonprofit organizations report their finances to the U.S. Internal Revenue Service. The IRS makes these disclosures available to the public, providing a unique opertunity to research the finances of tax-exempt organizations from giants like the [American Red Cross](https://projects.propublica.org/nonprofits/display_990/530196605/02_2020_prefixes_52-56%2F530196605_201906_990_2020020717122251) to small private charities like the [Ed Uihlein Family Foundation](https://projects.propublica.org/nonprofits/display_990/205723621/12_2020_prefixes_14-23%2F205723621_201912_990PF_2020120317465674).

Unfortunately, most form 990s are only available as scanned PDFs. This makes it very difficult to collect and analyze nonprofit data programmatically. ocris aims to fix that. 

## Before you start: efilings and more

Scanned PDFs are difficult to work with, especially when attempting to extract tabular data. 

Before you dive into this package, make sure it is right for your use case. 
* Would it be faster to bite the bullet and extract the data needed by hand?
* Is the data available through another source?

The IRS already makes select financial data available [in machine readable format](https://www.irs.gov/statistics/soi-tax-stats-annual-extract-of-tax-exempt-organization-financial-data) for many tax-exempt organizations. 

Many organizations file 990s electronically. The IRS makes these available as XML documents. [IRSx](https://github.com/jsfenfen/990-xml-reader) is a Python package for querying these XML files and reformatting them as easily workable csv, txt or json structures. Importantly, ocirs form component naming conventions are adopted from IRSx's [form index](http://www.irsx.info/).

[ProPublica's Nonprofit Explorer](https://projects.propublica.org/nonprofits/) is a searchable database of 14 million tax filings dating back to 2001. In addition to its user interface, there is an [API](https://projects.propublica.org/nonprofits/api) for requesting organization data and PDFs. The PDF urls returned by this API can be downloaded and placed directly into ocris.   

# ocirs: getting started

*IN PROGRESS* 

To get started with ocirs, simply clone this repo into your project 

[insert process for downloading ocirs and for making sure all dependencies are met, requirements.txt, tesseract in the path]

ocirs can operate as a stand-alone table extraction package. However, adding CascadeTabNet table detection can significantly improve the overall accuracy of the process. You'll need to perform some additional setup.

[insert process for setting up CascadeTabNet: mmdetection, download mmdet dependencies, mmdet setup, download CascadeTabNet model checkpoint]

# ocirs cookbook

Once you've downloaded ocirs, you're ready to get started. 

There are two classes to familiarize yourself with: `NineNinetyForm` and `NineNinetyPage`. The first is a Python object representing an entire 990 form. The second is an object representing an individual form page. Here is how to use them.

## NinetyNinetyForm

### **Creating a `NineNinetyForm` object:**
```
form_obj = NineNinetyForm(pdf_path, form_type, org_name, tax_period)
```
`form_obj` is the primary data structure that you can use to manipulate and analyze your form 990 PDFs.

### **Extracting page data from `NineNinetyForm`:**
```
pages = form_obj.extract_pages(save_path, save_type)
```
The result of this method is a list of `NineNinetyPage` objects, one for each page of the original PDF. By design, the `NineNinetyPage` objects will contain ocr data (as a pandas dataframe) for the associated PDF page. You can access the page list via the returned `pages` variable or with `form_obj.pages`. 

If you provide a `save_path` and a `save_type`, then ocirs will also save the ocr data to the specified location. 

### **Loading page data into `NineNinetyForm`**

Since it takes a long time to ocr images, ocirs has the option to upload pre-made ocr dataframes stored as pickles or CSVs.  

```
pages = form_obj.load_pages(data_path_list, page_index_list)
```
The result of this method, like `extract_pages()` is a list of `NineNinetyPage` objects associated with your `form_obj`. However, the instantiation time is much quicker.

`data_path_list` should be a list of file paths.  Data files must be derrived from 
`pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME)` 
and saved using pandas' `df.to_csv()` or `df.to_pickle()` dataframe methods. This mirrors the process used in `extract_pages()`. **If you don't follow these steps, then the table extraction process will not work.**

`page_index_list` is a list of integers whose value represents the page index of the original PDF. The elements in `data_path_list` must correspond with the elements in `page_index_list`.

**Pro-tip:** If you generated your data files using `extract_pages()` with a `save_path` and `save_type` you can generate a `data_path_list` and `page_index_list` like so:
```
data_path_list = glob.glob('save_path/**')
page_index_list = list(map(lambda x: x.split("_")[-1], data_path_list))
```

### **Searching for a specific form component**

```
form_component_pages = form_obj.search_form(form_component)
```

This will return a series NineNinetyPages identified by ocirs as belonging to that specific form component. You can also access these results with `form_obj.form_components`.

`form_component` should be a string and should reference a component described in IRSx's [form index](http://www.irsx.info/). For example, `"SkdIRcpntTbl"` on a classic 990 form will tell ocirs to search for, "Schedule I Part II, Grants and Other Assistance to Governments and Organizations in the United States".

Only a small subset of form components are searchable with ocirs out-of-the-box. To view what is available for each form type, `print(NineNinetyForm.valid_form_components)`. Always double check your program to make sure it's identifying the pages you want. 

### **Adding searchable form components**

You can teach ocirs how to search for other form components. Here's how you do it.

During the execution of your program, add a new component to the `NineNinetyForm.valid_form_component` dictionary.

```
NineNinetyForm.valid_form_components['990']["irsxComponent"] = 'Schedule Pi Part Rho, Accounting of baked goods delivered'
```

Lastly, you must add one or more search phrases to `NineNinetyForm.form_component_search_phrases`. ocirs uses these to fuzzysearch and match with text from the form's NineNinetyPage objects. 

```
NineNinetyForm.form_component_search_phrases['990']['irsxComponent'] = ["Accounting of baked goods delivered", "Pies sent, pies recieved"]
```

For the rest of your program's execution, you can now search with `form_obj.search_form("irsxComponent")`. 


### **Extracting table data from a Form component**

```
dfs = form_obj.extract_component_tables(form_component, merge, use_CascadeTabNet, table_type, extraction_method)
```

Returns a list of dataframes extracted from NineNinetyPage objects.

Combines `search_form()` (if not previously requested) and `NineNinetyPage().extract_tables()` to collect data from desired form pages.


If `merge=True`, a custom fuzzy merge function will be called on the list of returned dataframes and a single merged dataframe.

If no tables are extracted, it is possible ocirs could not extract tables from the desired pages. It's also possible that `search_form()` did not identify any pages for that form component.

## NineNinetyPage

You can also use ocirs to interact with 990 forms on a by-page basis. 

### **Creating a NineNinetyPage object**

```
page_obj = NineNinetyPage(image_path, data_path, parent_NineNinetyForm, index)
```

`page_obj` is the primary data structure that you can use to manipulate and analyze your form 990 pages.

Only `image_path` is required. By design, `NineNinetyPage` will ocr the image using pytesseract and store the output `pytesseract.Output.DATAFRAME` in `page_obj.ocr_dataframe`.

If a `data_path` is provided (and it will be if you are calling `form_obj.load_pages()`), then ocirs will load the data file and assign it to `ocr_dataframe`.

### **Requesting NineNinetyPage text**

Ocr data is stored in the NineNinetyPage object as a dataframe, but you can request the full text of a page as a string like so: 

```
page_text = page_obj.ocr_dataframe_to_text()
```

### **Extracting tables from a page**

```
table_dfs = page_obj.extract_tables(self, use_CascadeTabNet, table_type, extraction_method)
```

Returned will be a list of dataframes containing tabular data extracted from the page. You can also access this data *after* calling this function with `page_obj.tables`.

When you call `extract_component_tables()` on a NineNinetyForm object, what you are really doing is calling `page_obj.extract_tables()` on a series of page objects. 
