import os
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

def data_transformation_task(tasks):
    try:
        if not tasks:
            raise ValueError("Task configurations not found in XCom.")

        artifacts_dir = os.path.join(os.path.dirname(__file__), 'artifacts')
        train_path = os.path.join(artifacts_dir, 'train.csv')
        test_path = os.path.join(artifacts_dir, 'test.csv')

        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)

        for task_config in tasks:
            logging.info(f"Starting transformation for task: {task_config['task']}")

            numerical_cols = task_config['numerical_col']
            categorical_cols = task_config['categorical_col']

            label_encoders = {}
            for col in categorical_cols:
                le = CustomLabelEncoder()
                train_df[col] = le.fit_transform(train_df[col].astype(str))
                test_df[col] = le.transform(test_df[col].astype(str))
                label_encoders[col] = le

            numerical_pipeline = Pipeline([
                ("scaler", StandardScaler())
            ])

            categorical_pipeline = Pipeline([
                ("passthrough", "passthrough") 
            ])

            preprocessor = ColumnTransformer([
                ("num_pipeline", numerical_pipeline, numerical_cols),
                ("cat_pipeline", categorical_pipeline, categorical_cols)
            ])

            X_train = train_df[task_config['model_features']]
            y_train = train_df[task_config['target']]

            X_test = test_df[task_config['model_features']]
            y_test = test_df[task_config['target']]

            X_train_transformed = preprocessor.fit_transform(X_train)
            X_test_transformed = preprocessor.transform(X_test)

            transformed_data = {
                "X_train": X_train_transformed,
                "y_train": y_train,
                "X_test": X_test_transformed,
                "y_test": y_test
            }

            transformed_data_path = os.path.join(artifacts_dir, f"{task_config['task']}_transformed_data.pkl")
            with open(transformed_data_path, 'wb') as f:
                pickle.dump(transformed_data, f)

            logging.info(f"Data transformation completed for task: {task_config['task']}")
            logging.info(f"Transformed data saved to {transformed_data_path}")

            logging.info(f"X_train shape: {X_train_transformed.shape}")
            logging.info(f"X_test shape: {X_test_transformed.shape}")
            logging.info(f"y_train shape: {len(y_train)}")
            logging.info(f"y_test shape: {len(y_test)}")

    except Exception as e:
        logging.error(f"Error during data transformation: {e}")
        raise
