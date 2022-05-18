from datetime import datetime
import requests, os
import pandas as pd

def download_resource(url:str, file_path:str) -> str:
    """Downloads with requests library the url resource. By default it will save it ./data folder under the name of today's date (ex. 2022-5-2)

    Args:
        url (str): the url to the resource that should be downloaded
        file_path (str): the path where the resource should be downloaded to
    Returns:
        str: Success/Error message
    """
    if os.path.exists(file_path):
        return "ERROR, file already exists"
    else:    
        #write response (file) to data folder
        with open(file_path, "wb") as out_file:
            out_file.write(requests.get(url).content)
        return "Resource successfully downloaded to path: ", file_path

def clean_df(df:pd.DataFrame) -> pd.DataFrame: 

    """Cleans the given df: 
        - drops columns ["Nr.", "Sitecode", "Editor site", "Regie de publicitate"]
        - drops all rows where there are only NaN values
        - drops rows where Tip trafic is Nan, since these represent the totals for the site

    Args:
        df (pd.DataFrame): the original dataframe that needs to be cleaned

    Returns:
        pd.DataFrame: the cleaned df

    Obs. the changes are made inplace unless a df copy is passed to the function
    """

    #drop unneeded columns
    df.drop(["Nr.", "Sitecode", "Editor site", "Regie de publicitate"], axis=1, inplace=True)
    #drop blank rows
    df.dropna(axis=0, how='all', inplace=True)

    # drop rows where Tip trafic is Nan <=> these are the totals of the 3 trafic categories. These are unneeded, since totals can be generated from SQL too
    df.dropna(axis=0, subset=["Tip trafic"], inplace=True)

    return df

def normalize_df(df:pd.DataFrame, region_type:str, timestamp: datetime) -> pd.DataFrame:

    """Normalizes the given df: 
        - drops unneded cols and rows by cleaning df -> please refer to clean_df function for more detail
        - rename columns
        - stacks columns

    Args:
        df (pd.DataFrame): the original dataframe that needs to be normalized
        region_type (str): to specify the traffic's region: 'ro' or 'all'
        timestamp (datetime): the date in datetime format to that the data refers

    Returns:
        pd.DataFrame: the normalized df

    Obs. the changes are made inplace unless a df copy is passed to the function
    """

    #drop unneded cols and rows
    df = clean_df(df.copy(deep=True))

    #rename columns
    df.rename(columns={"Categorie": "category", "Site":"site", "Tip trafic": "traffic_type", "Contractor SATI": "SATI_contractor", "Afisari": "page_impression", "Vizite": "visit", "Clienti Unici": "unique_client"}, inplace=True)

    #stack columns so these have a single value in each row and multiple tags, speaking in InfluxDB terms
    df = df.set_index(['category', 'site', 'traffic_type', 'SATI_contractor']).stack().reset_index()
    df.rename(columns={"level_4": "value_type", 0: "field"}, inplace=True)

    df["traffic_region"] = region_type #column indicating that this traffic from all regions
    df["timestamp"] = timestamp #InfluxDB's "id", a datetime type value

    df.set_index("timestamp", inplace = True) 

    return df

def get_normalized_resource(resource_url:str, file_path:str, from_date:datetime, region_type:str) -> pd.DataFrame:

    print(file_path)

    #download the recource
    download_resource(resource_url, file_path)

    #normalize downloaded resourse
    df = pd.read_excel(file_path, engine='xlrd')
    print('read file')
    df = normalize_df(df.copy(deep=True), region_type, from_date)
    print('normalized file')
    return df
