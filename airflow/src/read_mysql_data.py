import os
import logging
import pandas as pd
from airflow.providers.mysql.hooks.mysql import MySqlHook

def read_sql_data():
    try:
        mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
        sql_query = "SELECT * FROM supplychain;"
        
        connection = mysql_hook.get_conn()
        df = pd.read_sql(sql_query, connection)
        logging.info("Data successfully fetched from MySQL.")

        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_data_path = os.path.join(temp_dir, 'raw_data.csv')
        df.to_csv(temp_data_path, index=False, header=True)
        logging.info(f"Raw data temporarily saved to {temp_data_path}.")

        return temp_data_path

    except Exception as e:
        logging.error(f"Error while reading data from MySQL: {e}")
        raise
