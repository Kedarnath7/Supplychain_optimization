import os
import sys
from src.supply.exception import CustomException
from src.supply.logger import logging
import pandas as pd
from dotenv import load_dotenv
import pymysql
import pickle

load_dotenv()

host=os.getenv("host")
user=os.getenv("user")
password=os.getenv("password")
db=os.getenv("db")


def read_sql_data():
    logging.info("reading sqldb started")
    try:
        mydb=pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db
        )
        logging.info("Connection established")
        df=pd.read_sql_query('Select * from supplychain',mydb)
        print(df.head())

        return df
        
    except Exception as ex:
        raise CustomException(ex,sys)

def save_object(file_path, obj):

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'wb') as file:
            pickle.dump(obj, file)
        
        logging.info(f"Object saved successfully at: {file_path}")
    
    except Exception as e:
        raise CustomException(f"Error occurred while saving object to {file_path}: {str(e)}", e)