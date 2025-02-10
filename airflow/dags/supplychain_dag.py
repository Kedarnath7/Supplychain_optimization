from airflow import DAG
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import os
import logging
import pickle
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error
from psycopg2 import Error as PostgresError
from sqlalchemy import create_engine
from airflow.hooks.base_hook import BaseHook

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), 'artifacts')
os.makedirs(ARTIFACTS_DIR, exist_ok=True)  # Ensure the directory exists
# Define default arguments
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
}

# Define the DAG
dag = DAG(
    'mysql_read_data',
    default_args=default_args,
    description='A DAG to read data from MySQL, perform data ingestion, transformation, store in PostgreSQL, and train models',
    schedule_interval='@daily',
    catchup=False,
)

# Function to read data from MySQL
def read_sql_data():
    try:
        # Use the MySqlHook to connect to the database
        mysql_hook = MySqlHook(mysql_conn_id='mysql_default')

        # Define your SQL query
        sql_query = "SELECT * FROM supplychain;"

        # Fetch data into a Pandas DataFrame
        connection = mysql_hook.get_conn()
        df = pd.read_sql(sql_query, connection)
        logging.info("Data successfully fetched from MySQL.")

        # Save the raw data to a temporary location
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_data_path = os.path.join(temp_dir, 'raw_data.csv')
        df.to_csv(temp_data_path, index=False, header=True)
        logging.info(f"Raw data temporarily saved to {temp_data_path}.")

        return temp_data_path

    except Exception as e:
        logging.error(f"Error while reading data from MySQL: {e}")
        raise

# Function to perform data ingestion
def data_ingestion_task(**kwargs):
    try:
        # Retrieve the temporary data path from the previous task
        ti = kwargs['ti']
        temp_data_path = ti.xcom_pull(task_ids='read_sql_data')

        # Define paths for artifacts
        artifacts_dir = os.path.join(os.path.dirname(__file__), 'artifacts')
        os.makedirs(artifacts_dir, exist_ok=True)

        raw_data_path = os.path.join(artifacts_dir, 'raw.csv')
        train_data_path = os.path.join(artifacts_dir, 'train.csv')
        test_data_path = os.path.join(artifacts_dir, 'test.csv')

        # Load the raw data from the temporary location
        df = pd.read_csv(temp_data_path)
        logging.info("Raw data loaded from temporary location.")

        # Save raw data to artifacts
        df.to_csv(raw_data_path, index=False, header=True)
        logging.info(f"Raw data saved to {raw_data_path}.")

        # Split data into train and test sets
        train_set, test_set = train_test_split(df, test_size=0.2, random_state=42)
        train_set.to_csv(train_data_path, index=False, header=True)
        test_set.to_csv(test_data_path, index=False, header=True)
        logging.info(f"Train data saved to {train_data_path}.")
        logging.info(f"Test data saved to {test_data_path}.")

        logging.info("Data ingestion completed successfully.")

    except Exception as e:
        logging.error(f"Error during data ingestion: {e}")
        raise

# Function to get task configuration
def get_task_config(**kwargs):
    try:
        # Define the task configuration
        tasks = [
            {
                "task": "late_delivery_risk_prediction",
                "numerical_col": ["Days_for_shipping_real", "Days_for_shipment_scheduled", "Product_Price", "Order_Item_Quantity", "Order_Item_Discount_Rate"],
                "categorical_col": ["Shipping_Mode", "Category_Id", "Category_Name", "Order_State", "Order_Region", "Order_Country"],
                "target": "Late_delivery_risk",
                "model_features": ["Category_Id", "Category_Name", "Days_for_shipping_real", "Days_for_shipment_scheduled", "Shipping_Mode", "Order_State", "Order_Region", "Order_Country", "Product_Price", "Order_Item_Quantity", "Order_Item_Discount_Rate"],
                "task_type": "classification",
            },
            {
                "task": "order_profit_prediction",
                "numerical_col": ['Sales', 'Product_Price', 'Order_Item_Quantity', 'Order_Item_Discount_Rate', 'Profit_Margin'],
                "categorical_col": ['Shipping_Mode', 'Order_State', 'Order_Country', 'Customer_Segment'],
                "target": "Order_Profit_Per_Order",
                "model_features": ['Sales', 'Product_Price', 'Order_Item_Quantity', 'Order_Item_Discount_Rate', 'Profit_Margin', 'Shipping_Mode', 'Order_State', 'Order_Country', 'Customer_Segment'],
                "task_type": "regression",
            },
            {
                "task": "shipping_time_prediction",
                "numerical_col": ["Days_for_shipment_scheduled", "Product_Price", "Order_Item_Quantity", "Order_Item_Discount_Rate"],
                "categorical_col": ["Shipping_Mode", "Category_Id", "Category_Name", "Order_State", "Order_Region", "Order_Country"],
                "target": "Days_for_shipping_real",
                "model_features": ["Category_Id", "Category_Name", "Days_for_shipment_scheduled", "Shipping_Mode", "Order_State", "Order_Region", "Order_Country", "Product_Price", "Order_Item_Quantity", "Order_Item_Discount_Rate"],
                "task_type": "regression",
            }
        ]

        # Push the task configuration to XCom
        ti = kwargs['ti']
        ti.xcom_push(key='tasks', value=tasks)  # Push all tasks to XCom
        logging.info(f"Task configurations loaded: {[task['task'] for task in tasks]}")

    except Exception as e:
        logging.error(f"Error while loading task configuration: {e}")
        raise

from sklearn.preprocessing import LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import pandas as pd
import logging
import pickle
import numpy as np
class CustomLabelEncoder(LabelEncoder):
    def transform(self, y):
        # Handle unseen labels by assigning them a default value (-1)
        return np.array([self.classes_.tolist().index(val) if val in self.classes_ else -1 for val in y])

def data_transformation_task(**kwargs):
    try:
        ti = kwargs['ti']
        tasks = ti.xcom_pull(task_ids='get_task_config', key='tasks')

        # Check if tasks is None
        if tasks is None:
            raise ValueError("Task configurations not found in XCom. Ensure 'get_task_config' task runs successfully.")

        # Load the train and test data
        artifacts_dir = os.path.join(os.path.dirname(__file__), 'artifacts')
        train_path = os.path.join(artifacts_dir, 'train.csv')
        test_path = os.path.join(artifacts_dir, 'test.csv')
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)

        # Loop through each task and perform transformations
        for task_config in tasks:
            logging.info(f"Starting transformation for task: {task_config['task']}")

            # Define the numerical and categorical columns
            numerical_cols = task_config['numerical_col']
            categorical_cols = task_config['categorical_col']

            # Use CustomLabelEncoder for categorical columns
            label_encoders = {}
            for col in categorical_cols:
                le = CustomLabelEncoder()
                train_df[col] = le.fit_transform(train_df[col].astype(str))  # Convert to string to handle mixed types
                test_df[col] = le.transform(test_df[col].astype(str))  # Convert to string to handle mixed types
                label_encoders[col] = le

            # Create the transformation pipelines
            numerical_pipeline = Pipeline([
                ("scaler", StandardScaler())
            ])

            # For categorical columns, use a passthrough pipeline (no additional transformation needed)
            categorical_pipeline = Pipeline([
                ("passthrough", "passthrough")
            ])

            # Combine the pipelines using ColumnTransformer
            preprocessor = ColumnTransformer([
                ("num_pipeline", numerical_pipeline, numerical_cols),
                ("cat_pipeline", categorical_pipeline, categorical_cols)  # Include categorical columns
            ])

            # Transform the data
            X_train = train_df[task_config['model_features']]
            y_train = train_df[task_config['target']]

            X_test = test_df[task_config['model_features']]
            y_test = test_df[task_config['target']]

            X_train_transformed = preprocessor.fit_transform(X_train)
            X_test_transformed = preprocessor.transform(X_test)

            # Store the transformed data in a dictionary
            transformed_data = {
                "X_train": X_train_transformed,
                "y_train": y_train,
                "X_test": X_test_transformed,
                "y_test": y_test
            }

            # Save the transformed data to a file
            transformed_data_path = os.path.join(artifacts_dir, f"{task_config['task']}_transformed_data.pkl")
            with open(transformed_data_path, 'wb') as f:
                pickle.dump(transformed_data, f)

            logging.info(f"Data transformation completed for task: {task_config['task']}")
            logging.info(f"Transformed data saved to {transformed_data_path}")

            # Log the shapes of the transformed data
            logging.info(f"X_train shape: {X_train_transformed.shape}")
            logging.info(f"X_test shape: {X_test_transformed.shape}")
            logging.info(f"y_train shape: {len(y_train)}")
            logging.info(f"y_test shape: {len(y_test)}")

    except Exception as e:
        logging.error(f"Error during data transformation: {e}")
        raise

#post

import tempfile
import psycopg2
import os
import logging
import pickle
import pandas as pd
from sqlalchemy import create_engine, Table, Column, Float, MetaData
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
            raise ValueError("Task configurations not found in XCom. Ensure 'get_task_config' task runs successfully.")

        for task_config in tasks:
            task_name = task_config['task']
            transformed_data_path = os.path.join(ARTIFACTS_DIR, f"{task_name}_transformed_data.pkl")

            if not os.path.exists(transformed_data_path):
                raise FileNotFoundError(f"Transformed data file not found: {transformed_data_path}")

            # Load transformed data
            with open(transformed_data_path, 'rb') as f:
                transformed_data = pickle.load(f)

            # Logging data shapes and sample content
            logging.info(f"Task: {task_name}")
            logging.info(f"X_train shape: {transformed_data['X_train'].shape}, X_test shape: {transformed_data['X_test'].shape}")
            logging.info(f"y_train size: {len(transformed_data['y_train'])}, y_test size: {len(transformed_data['y_test'])}")
            logging.info(f"X_train sample: {transformed_data['X_train'][:5]}")
            logging.info(f"y_train sample: {transformed_data['y_train'][:5]}")

            # Initialize PostgreSQL connection
            pg_hook = PostgresHook(postgres_conn_id='postgres_default')
            conn = pg_hook.get_conn()
            cursor = conn.cursor()

            schema_name = "airflow_schema"
            train_table_name = f"stg_{task_name}_train"
            test_table_name = f"stg_{task_name}_test"

            # Drop existing tables if they exist
            drop_table_sql = f"""
                DROP TABLE IF EXISTS {schema_name}.{train_table_name};
                DROP TABLE IF EXISTS {schema_name}.{test_table_name};
            """
            cursor.execute(drop_table_sql)
            conn.commit()

            # Create new tables with the correct schema
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

            # Insert train data
            train_insert_sql = f"""
                INSERT INTO {schema_name}.{train_table_name} (
                    {', '.join([f'feature_{i}' for i in range(num_features)])}, y_train
                ) VALUES ({', '.join(['%s'] * (num_features + 1))});
            """
            # Convert NumPy arrays to native Python types
            train_values = [
                tuple(map(float, row)) + (float(transformed_data['y_train'][i]),)  # Convert to float
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

            # Insert test data
            test_insert_sql = f"""
                INSERT INTO {schema_name}.{test_table_name} (
                    {', '.join([f'feature_{i}' for i in range(num_features)])}, y_test
                ) VALUES ({', '.join(['%s'] * (num_features + 1))});
            """
            # Convert NumPy arrays to native Python types
            test_values = [
                tuple(map(float, row)) + (float(transformed_data['y_test'][i]),)  # Convert to float
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

#train
def train_models(**kwargs):
    try:
        ti = kwargs['ti']
        tasks = ti.xcom_pull(task_ids='get_task_config', key='tasks')

        # Check if tasks is None
        if tasks is None:
            raise ValueError("Task configurations not found in XCom. Ensure 'get_task_config' task runs successfully.")

        # Load data from PostgreSQL and train models
        postgres_hook = PostgresHook(postgres_conn_id='postgres_default')
        conn = postgres_hook.get_conn()

        for task_config in tasks:
            logging.info(f"Training model for task: {task_config['task']}")

            # Define table names
            schema_name = "airflow_schema"
            train_table_name = f"stg_{task_config['task']}_train"
            test_table_name = f"stg_{task_config['task']}_test"

            # Load train and test data from PostgreSQL
            train_df = pd.read_sql(f"SELECT * FROM {schema_name}.{train_table_name}", conn)
            test_df = pd.read_sql(f"SELECT * FROM {schema_name}.{test_table_name}", conn)

            # Split features and target
            X_train = train_df.iloc[:, :-1]  # All columns except the last one are features
            y_train = train_df.iloc[:, -1]   # Last column is the target
            X_test = test_df.iloc[:, :-1]    # All columns except the last one are features
            y_test = test_df.iloc[:, -1]     # Last column is the target

            # Train the model based on task type
            if task_config['task_type'] == 'classification':
                model = RandomForestClassifier()
            elif task_config['task_type'] == 'regression':
                model = RandomForestRegressor()
            else:
                raise ValueError(f"Unknown task type: {task_config['task_type']}")

            # Fit the model
            model.fit(X_train, y_train)

            # Evaluate the model
            y_pred = model.predict(X_test)
            if task_config['task_type'] == 'classification':
                accuracy = accuracy_score(y_test, y_pred)
                logging.info(f"Model accuracy for {task_config['task']}: {accuracy}")
            elif task_config['task_type'] == 'regression':
                mse = mean_squared_error(y_test, y_pred)
                logging.info(f"Model MSE for {task_config['task']}: {mse}")

            # Save the model
            model_path = os.path.join(ARTIFACTS_DIR, f"{task_config['task']}_model.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            logging.info(f"Model saved to {model_path}")

        conn.close()

    except Exception as e:
        logging.error(f"Error during model training: {e}")
        raise

# Task 1: Read data from MySQL
read_data_task = PythonOperator(
    task_id='read_sql_data',
    python_callable=read_sql_data,
    dag=dag,
)

# Task 2: Perform data ingestion
ingestion_task = PythonOperator(
    task_id='data_ingestion',
    python_callable=data_ingestion_task,
    provide_context=True,  # Passes the context (including XCom) to the function
    dag=dag,
)

# Task 3: Get task configuration
get_task_config_task = PythonOperator(
    task_id='get_task_config',
    python_callable=get_task_config,
    provide_context=True,
    dag=dag,
)

# Task 4: Perform data transformation
transformation_task = PythonOperator(
    task_id='data_transformation',
    python_callable=data_transformation_task,
    provide_context=True,
    dag=dag,
)

# Task 5: Store transformed data in PostgreSQL
store_in_postgres_task = PythonOperator(
    task_id='store_in_postgres',
    python_callable=store_in_postgres,
    provide_context=True,
    dag=dag,
)

# Task 6: Train models using data from PostgreSQL
train_models_task = PythonOperator(
    task_id='train_models',
    python_callable=train_models,
    provide_context=True,
    dag=dag,
)

# Set task dependencies
read_data_task >> ingestion_task >> get_task_config_task >> transformation_task >> store_in_postgres_task >> train_models_task
