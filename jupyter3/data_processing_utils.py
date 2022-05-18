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
        raise Exception("Resource was not downloaded, file already exists")
    else:    
        #write response (file) to data folder
        with open(file_path, "wb") as out_file:
            out_file.write(requests.get(url).content) #data download is need for safety reasons
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

def normalize_df(df:pd.DataFrame, timestamp: datetime) -> pd.DataFrame:

    """Normalizes the given df: 
        - drops unneded cols and rows by cleaning df -> please refer to clean_df function for more detail
        - rename columns
        - stacks columns

    Args:
        df (pd.DataFrame): the original dataframe that needs to be normalized
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

    df["timestamp"] = timestamp #InfluxDB's "id", a datetime type value

    df.set_index("timestamp", inplace = True) 

    return df


def calculate_nonRO_traffic(df:pd.DataFrame, df_ro:pd.DataFrame, timestamp:datetime) -> pd.DataFrame:
    """
    Calculates from all- and Romanian traffic the traffic from outside of Romania.
    
    Args:
        df (pd.DataFrame): normalized df with worldwide traffic (please refer to normalize_df function with)
        df_ro (pd.DataFrame): normalized df with Romanian traffic (please refer to normalize_df function with)
        timestamp (datetime): the date in datetime format to that the data refers
    
    Returns:
        pd.DataFrame: the normalized df referring to non-Romanian traffic
    """
    
    #map the Romanian traffic to the sites 
    df_m = df.merge(df_ro.set_index(['category', 'site', 'traffic_type', 'SATI_contractor', 'value_type']), on=['category', 'site', 'traffic_type', 'SATI_contractor', 'value_type'], how="inner")

    #calculate the diff between worldwide traffic and Romanian traffic => we get the non-Romanian traffic
    df_m["value"] = df_m["field_x"] - df_m["field_y"]
    
    #normalize df: drop unneeded cols, traffic_region = "non-RO" and make timestamp index
    df_m.drop(["field_x", "traffic_region_x", "field_y", "traffic_region_y"], axis=1, inplace=True)

    df_m["timestamp"] = timestamp
    df_m.set_index("timestamp", inplace=True)
    df_m.rename(columns={"value": "field"}, inplace=True)
    return df_m


def get_normalized_resource(resource_url:str, file_path:str, from_date:datetime) -> pd.DataFrame:
    """
    Downloads from resource_url the excel file containing the site traffic. This will be normalized too.
    
    Args:
        resource_url (str): the url to the excel file that will be scraped
        file_path (str): the local path to that the excel will be saved
        from_date (datetime): the date to that data refers - this will be the index of influx db
    
    Returns:
        pd.DataFrame: the normalized df that can be sent to InfluxDB
    """

    #download the recource
    download_resource(resource_url, file_path)

    #normalize downloaded resourse
    df = pd.read_excel(file_path, engine='xlrd')

    df = normalize_df(df.copy(deep=True), from_date)
    
    return df
