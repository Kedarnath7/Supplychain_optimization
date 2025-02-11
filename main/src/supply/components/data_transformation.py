
import sys
import os
from dataclasses import dataclass
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from src.supply.exception import CustomException
from src.supply.logger import logging
from src.supply.utils import save_object
from sklearn.pipeline import Pipeline

@dataclass
class DataTransformationConfig:
    preprocessor_file_path: str=os.path.join('artifacts', 'preprocessor.pkl')

class DataTransformation:
    def __init__(self):
        self.config=DataTransformationConfig()

    def get_data_transformer(self, features_config):
        try:
            pipelines={}

            for target, config in features_config.items():
                logging.info(f"Creating pipeline for target : {target}")

                num_pipeline =Pipeline([
                    ("scalar", StandardScaler())
                ])

                cat_pipeline = Pipeline([
                    ("one_hot_encoder", OneHotEncoder(handle_unknown="ignore"))
                ])

                logging.info(f"Numerical columns: {config['numerical']}")
                logging.info(f"Categorical columns: {config['categorical']}")
            
                preprocessor = ColumnTransformer([
                    ("num_pipe", num_pipeline, config['numerical']),
                    ("cat_pipe", cat_pipeline, config['categorical'])
                ])

                pipelines[target] = preprocessor
            
            return pipelines
        except Exception as e:
            raise CustomException(e, sys)
        
    def initiate_data_transformation(self, train_path, test_path, features_config):
            
            try:
                train_df=pd.read_csv(train_path)
                test_df=pd.read_csv(test_path)

                pipelines=self.get_data_transformer(features_config)
                transformed_data = {}

                for target, pipeline in pipelines.items():
                     logging.info(f"Transforming data for target: {target}")

                     X_train=train_df[features_config[target]['features']]
                     y_train=train_df[target]

                     X_test=test_df[features_config[target]['features']]
                     y_test=test_df[target]

                     X_train_transformed=pipeline.fit_transform(X_train)
                     X_test_transformed=pipeline.transform(X_test)


                     transformed_data[target] = {
                         "X_train": X_train_transformed,
                         "y_train": y_train,
                         "X_test": X_test_transformed,
                         "y_test": y_test
                         }
                     
                     save_object(os.path.join('artifacts', f'{target}_preprocessor.pkl'), pipeline)

                return transformed_data
            except Exception as e:
                raise CustomException(e, sys)
