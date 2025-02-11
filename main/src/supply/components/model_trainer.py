import sys
import os
from dataclasses import dataclass
from src.supply.exception import CustomException
from src.supply.logger import logging
from src.supply.utils import save_object
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_squared_error, accuracy_score
from xgboost import XGBClassifier, XGBRegressor
import pickle

@dataclass
class ModelTrainerConfig:
    model_file_path:str = os.path.join('artifacts','models')

class ModelTrainer:
    def __init__(self):
        self.config = ModelTrainerConfig()

    def train_model(self, transformed_data, target, task_type):
        try:
            logging.info(f"Training model for target: {target}, task type: {task_type}")

            X_train = transformed_data['X_train']
            y_train = transformed_data['y_train']
            X_test = transformed_data['X_test']
            y_test = transformed_data['y_test']


            if task_type == "regression":
                model = XGBRegressor()
            elif task_type == "classification":
                model = RandomForestClassifier()
            else:
                raise ValueError(f"Unsupported task type : {task_type}")
            
            model.fit(X_train, y_train)
            logging.info(f"Model training complete for target: {target}")

            if task_type == "regression":
                y_pred = model.predict(X_test)
                score = mean_squared_error(y_test,y_pred)
                logging.info(f"MSE for {target}: {score}")
            elif task_type == "classification":
                y_pred = model.predict(X_test)
                score = accuracy_score(y_test, y_pred)
                logging.info(f"Accuracy for {target}: {score}")

            model_path = os.path.join(self.config.model_file_path, f"{target}_model.pkl")
            save_object(model_path, model)

            return score, model_path

        except Exception as e:
            raise CustomException(e, sys)