
import pandas as pd
import numpy as np
from fuzzywuzzy import process


def clean_dataframe(df):
    
    #First, we replace empty cells (" ", "") with np.nan 
    df.replace(to_replace=[" ",""], value=np.nan, inplace=True)

    # Then drop totally empty rows and columns, no data in them and they will not be useful
    df.dropna(how='all', axis=1, inplace=True)
    df.dropna(how='all', inplace = True) 


    return df



def merge_dataframes(dataframe_list):
    '''
    Takes a list of dataframes and merges them into a single dataframe

    Intended to be uses as a final step after running NineNinetyMagic().extract_component_table(), which produces
    a list of dataframes extracted from a 990 form component
    '''
    
    
    #First we clean up the dataframe list by removing totally empty columns and rows from the dataframes inside
    dataframe_list = list(map(clean_dataframe, dataframe_list))

    
    # Next, we need to figure out what the column names are gonna be
    # Create a list to store column names, build out list and fuzzy match column names
    column_names = []
    #Create a dict for easy translation to primary column names
    column_translator = {} 
    for df in dataframe_list:

        # print(df)

        df_columns = df.iloc[0]
   
        for column_name in df_columns:

            # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$44")
            # print(column_name)
            # print(column_names)
            # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            
            match = process.extract(column_name, column_names)
            if not match: #Checks if process.extract returns nothing
                column_names.append(column_name)
                column_translator[column_name] = column_name
            else:
                if match[0][1] > 96: #Means we already have that column name stored
                    column_translator[column_name] = match[0][0]
                    
                else:
                    column_names.append(column_name)
                    column_translator[column_name] = column_name
              
    #Now that we have a list of column names. We can instantiate a new dataframe with those column names and begin building the new combined df
    # print(column_names)
    merged_df = pd.DataFrame(columns=column_names)

    # print(dataframe_list)
    for df in dataframe_list:
        # print(df)
        #First, update the dataframe with the new standardized column names
        #We can do this by leveraging the column translator to append the appropriate value to the column list 
        merged_columns = [] 
        df_columns = df.iloc[0]
        for column in df_columns:
            merged_columns.append(column_translator[column])

        df.columns = merged_columns

        # print(df.columns)


        #Next, all that's left to do is concat the dataframe to our merged list
        merged_df = pd.concat([merged_df, df.iloc[1:]], ignore_index=True, axis=0)
      

    
    return merged_df
    
    
