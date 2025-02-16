import os
import sys
import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

AIRFLOW_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AIRFLOW_HOME)

from src.read_mysql_data import read_sql_data
from src.data_ingestion import data_ingestion_task
from src.config.config_loader import load_task_config
from src.data_transformation import data_transformation_task
from src.load_to_postgres import store_in_postgres
from src.model_training import train_models

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 12),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

#DAG
dag = DAG(
    'supplychain_etl',
    default_args=default_args,
    description='ETL pipeline for supply chain data',
    schedule_interval=timedelta(days=1),
    catchup=False
)

#1.Read SQL Data
read_sql_task = PythonOperator(
    task_id='read_sql_data',
    python_callable=read_sql_data,
    dag=dag
)

#2.Data Ingestion
def wrapper_data_ingestion(**kwargs):
    ti = kwargs['ti']
    temp_data_path = ti.xcom_pull(task_ids='read_sql_data')
    data_ingestion_task(temp_data_path)

data_ingestion = PythonOperator(
    task_id='data_ingestion',
    python_callable=wrapper_data_ingestion,
    provide_context=True,
    dag=dag
)

#3.Get Task Configurations
def get_task_config(**kwargs):
    ti = kwargs['ti']
    tasks = load_task_config()
    ti.xcom_push(key='tasks', value=tasks)
    logging.info(f"Task configurations loaded: {[task['task'] for task in tasks]}")

task_config = PythonOperator(
    task_id='get_task_config',
    python_callable=get_task_config,
    provide_context=True,
    dag=dag
)

#4.Data Transformation
def wrapper_data_transformation(**kwargs):
    ti = kwargs['ti']
    tasks = ti.xcom_pull(task_ids='get_task_config', key='tasks')
    data_transformation_task(tasks)

data_transformation = PythonOperator(
    task_id='data_transformation',
    python_callable=wrapper_data_transformation,
    provide_context=True,
    dag=dag
)

#5.Store Data in PostgreSQL
store_postgres = PythonOperator(
    task_id='store_to_postgres',
    python_callable=store_in_postgres,
    provide_context=True,
    dag=dag
)

#6.Train Models
def wrapper_train_models(**kwargs):
    ti = kwargs['ti']
    tasks = ti.xcom_pull(task_ids='get_task_config', key='tasks')
    
    if not tasks:
        raise ValueError("Task configurations not found. Ensure 'get_task_config' task runs successfully.")

    logging.info("Starting model training process...")
    train_models(tasks)
    logging.info("Model training completed successfully.")

train_model_task = PythonOperator(
    task_id='train_models',
    python_callable=wrapper_train_models,
    dag=dag
)

#Order
read_sql_task >> data_ingestion >> task_config >> data_transformation >> store_postgres >> train_model_task
