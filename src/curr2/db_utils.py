from influxdb import DataFrameClient
import pandas as pd

def get_data_frame_client(host: str, dbname: str) -> DataFrameClient:
    """
    Gets an influxdb.DataFrameClient with the specifications:
    * user = 'root'
    * password = 'root'
    * host = <host arg value>
    * dbname = <dbname arg value>
    """
    user = 'root'
    password = 'root'
    host=host
    port=8086
    dbname=dbname
    
    return DataFrameClient(host, port, user, password, dbname)

def write_data_to_db(client: DataFrameClient, data_df: pd.DataFrame, measurement: str) -> None:
    """
    Writes data to InfluxDB
    
    Args:
        client (influxdb.DataFrameClient)
        data_df (pd.DataFrame): the dataframe that needs to be written to InfluxDB
        measurement (str): the database's measurement (table) name
        
    """
    client.write_points(data_df, measurement, protocol = 'line', field_columns = ["field"], tag_columns = ["category", "site", "traffic_type", "SATI_contractor", "value_type", "traffic_region"])