from influxdb import DataFrameClient

def get_data_frame_client(host: str, dbname: str) -> DataFrameClient:
    user = 'root'
    password = 'root'
    host=host
    port=8086
    dbname=dbname #az en adatbazis nevem
    protocol = 'line' #json
    return DataFrameClient(host, port, user, password, dbname)

def write_data_to_db(client: DataFrameClient, data_df, measurement: str) -> None:
    client.write_points(data_df, measurement, protocol = 'line', field_columns = ["field"], tag_columns = ["category", "site", "traffic_type", "SATI_contractor", "value_type", "traffic_region"])