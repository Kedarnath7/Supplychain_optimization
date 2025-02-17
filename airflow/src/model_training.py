import os
import logging
import pickle
import mlflow
import mlflow.sklearn
import pandas as pd
import dagshub
import requests
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score
)
'''

import warnings
import urllib3

warnings.filterwarnings("ignore", category=UserWarning)
warnings.simplefilter("ignore")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ["PYTHONWARNINGS"] = "ignore"

'''

dagshub.init(repo_owner='kedarnathpinjala11', repo_name='Supplychain_optimization', mlflow=True)
os.environ['MLFLOW_TRACKING_INSECURE_TLS'] = 'true'
requests.get("https://dagshub.com", verify=True)

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), 'artifacts')

def train_models(tasks):
    try:
        if not tasks:
            raise ValueError("Task configurations not found.")

        postgres_hook = PostgresHook(postgres_conn_id='postgres_default')
        conn = postgres_hook.get_conn()

        for task_config in tasks:
            logging.info(f"Training model for task: {task_config['task']}")

            schema_name = "airflow_schema"
            train_table = f"stg_{task_config['task']}_train"
            test_table = f"stg_{task_config['task']}_test"

            train_df = pd.read_sql(f"SELECT * FROM {schema_name}.{train_table}", conn)
            test_df = pd.read_sql(f"SELECT * FROM {schema_name}.{test_table}", conn)

            X_train, y_train = train_df.iloc[:, :-1], train_df.iloc[:, -1]
            X_test, y_test = test_df.iloc[:, :-1], test_df.iloc[:, -1]

            if task_config['task_type'] == 'classification':
                models = {
                    "RandomForestClassifier": RandomForestClassifier(),
                    "LogisticRegression": LogisticRegression(max_iter=500),
                    "XGBoostClassifier": XGBClassifier(use_label_encoder=False, eval_metric="logloss"),
                }
            elif task_config['task_type'] == 'regression':
                models = {
                    "RandomForestRegressor": RandomForestRegressor(),
                    "LinearRegression": LinearRegression(),
                    "XGBoostRegressor": XGBRegressor(),
                }
            else:
                raise ValueError(f"Unknown task type: {task_config['task_type']}")
            
            for model_name, model in models.items():
                with mlflow.start_run(run_name=f"{task_config['task']}_{model_name}"):
                    mlflow.log_params({"task": task_config["task"], "task_type": task_config["task_type"], "model": model_name})

                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)

                    if task_config['task_type'] == 'classification':
                        metrics = {
                            "accuracy": accuracy_score(y_test, y_pred),
                            "precision": precision_score(y_test, y_pred, average='weighted', zero_division=0),
                            "recall": recall_score(y_test, y_pred, average='weighted', zero_division=0),
                            "f1_score": f1_score(y_test, y_pred, average='weighted', zero_division=0),
                        }
                    else:
                        metrics = {
                            "mse": mean_squared_error(y_test, y_pred),
                            "rmse": mean_squared_error(y_test, y_pred) ** 0.5,
                            "mae": mean_absolute_error(y_test, y_pred),
                            "r2_score": r2_score(y_test, y_pred),
                        }

                    for key, value in metrics.items():
                        mlflow.log_metric(key, value)
                        logging.info(f"{key} for {task_config['task']} ({model_name}): {value}")

                    model_path = os.path.join(ARTIFACTS_DIR, f"{task_config['task']}_{model_name}.pkl")
                    with open(model_path, 'wb') as f:
                        pickle.dump(model, f)

                    #log models in mlflow only when required
                    #mlflow.sklearn.log_model(model, f"{task_config['task']}_{model_name}", pip_requirements="airflow/requirements.txt")
                    #logging.info(f"Model {model_name} saved and logged at {model_path}")
    except Exception as e:
        logging.error(f"Error during model training: {e}")
        raise
    finally:
        conn.close()