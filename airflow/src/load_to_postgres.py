import tempfile
import psycopg2
import os
import logging
import pickle
import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import TaskInstance
import psutil
import os
import logging

def store_in_postgres(**kwargs):
    try:
        ti: TaskInstance = kwargs['ti']
        tasks = ti.xcom_pull(task_ids='get_task_config', key='tasks')

        if tasks is None:
            raise ValueError("Task configurations not found in XCom.")

        ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), 'artifacts')
        for task_config in tasks:
            task_name = task_config['task']
            transformed_data_path = os.path.join(ARTIFACTS_DIR, f"{task_name}_transformed_data.pkl")

            if not os.path.exists(transformed_data_path):
                raise FileNotFoundError(f"Transformed data file not found: {transformed_data_path}")

            with open(transformed_data_path, 'rb') as f:
                transformed_data = pickle.load(f)

            logging.info(f"Task: {task_name}")
            logging.info(f"X_train shape: {transformed_data['X_train'].shape}, X_test shape: {transformed_data['X_test'].shape}")
            logging.info(f"y_train size: {len(transformed_data['y_train'])}, y_test size: {len(transformed_data['y_test'])}")
            logging.info(f"X_train sample: {transformed_data['X_train'][:5]}")
            logging.info(f"y_train sample: {transformed_data['y_train'][:5]}")

            pg_hook = PostgresHook(postgres_conn_id='postgres_default')
            conn = pg_hook.get_conn()
            cursor = conn.cursor()

            schema_name = "airflow_schema"
            train_table_name = f"stg_{task_name}_train"
            test_table_name = f"stg_{task_name}_test"

            drop_table_sql = f"""
                DROP TABLE IF EXISTS {schema_name}.{train_table_name};
                DROP TABLE IF EXISTS {schema_name}.{test_table_name};
            """
            cursor.execute(drop_table_sql)
            conn.commit()

            num_features = transformed_data['X_train'].shape[1]
            create_train_table_sql = f"""
                CREATE TABLE {schema_name}.{train_table_name} (
                    {', '.join([f'feature_{i} FLOAT' for i in range(num_features)])},
                    y_train FLOAT
                );
            """
            create_test_table_sql = f"""
                CREATE TABLE {schema_name}.{test_table_name} (
                    {', '.join([f'feature_{i} FLOAT' for i in range(num_features)])},
                    y_test FLOAT
                );
            """
            cursor.execute(create_train_table_sql)
            cursor.execute(create_test_table_sql)
            conn.commit()

            train_insert_sql = f"""
                INSERT INTO {schema_name}.{train_table_name} (
                    {', '.join([f'feature_{i}' for i in range(num_features)])}, y_train
                ) VALUES ({', '.join(['%s'] * (num_features + 1))});
            """
            train_values = [
                tuple(map(float, row)) + (float(transformed_data['y_train'][i]),) 
                for i, row in enumerate(transformed_data['X_train'])
            ]
            try:
                logging.info(f"Inserting train data into {schema_name}.{train_table_name}")
                cursor.executemany(train_insert_sql, train_values)
                conn.commit()
                logging.info(f"Train data successfully stored in: {schema_name}.{train_table_name}")
            except Exception as e:
                logging.error(f"Error inserting train data: {e}")
                conn.rollback()
                raise

            test_insert_sql = f"""
                INSERT INTO {schema_name}.{test_table_name} (
                    {', '.join([f'feature_{i}' for i in range(num_features)])}, y_test
                ) VALUES ({', '.join(['%s'] * (num_features + 1))});
            """
            test_values = [
                tuple(map(float, row)) + (float(transformed_data['y_test'][i]),) 
                for i, row in enumerate(transformed_data['X_test'])
            ]
            try:
                logging.info(f"Inserting test data into {schema_name}.{test_table_name}")
                cursor.executemany(test_insert_sql, test_values)
                conn.commit()
                logging.info(f"Test data successfully stored in: {schema_name}.{test_table_name}")
            except Exception as e:
                logging.error(f"Error inserting test data: {e}")
                conn.rollback()
                raise

            cursor.close()
            conn.close()

        logging.info("All data successfully stored in PostgreSQL.")
        return {"status": "success", "message": "Data imported successfully into PostgreSQL."}

    except Exception as e:
        memory_usage_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2
        logging.error(f"Error while storing data in PostgreSQL: {e}")
        logging.error(f"Memory usage: {memory_usage_mb:.2f} MB")
        raise
