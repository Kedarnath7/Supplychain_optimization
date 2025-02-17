import os
import logging
import pandas as pd
from sklearn.model_selection import train_test_split

def data_ingestion_task(temp_data_path):
    try:
        artifacts_dir = os.path.join(os.path.dirname(__file__), 'artifacts')
        os.makedirs(artifacts_dir, exist_ok=True)

        raw_data_path = os.path.join(artifacts_dir, 'raw.csv')
        train_data_path = os.path.join(artifacts_dir, 'train.csv')
        test_data_path = os.path.join(artifacts_dir, 'test.csv')

        df = pd.read_csv(temp_data_path)
        logging.info("Raw data loaded from temporary location.")

        df.to_csv(raw_data_path, index=False, header=True)
        logging.info(f"Raw data saved to {raw_data_path}.")

        train_set, test_set = train_test_split(df, test_size=0.2, random_state=42)
        train_set.to_csv(train_data_path, index=False, header=True)
        test_set.to_csv(test_data_path, index=False, header=True)

        logging.info(f"Train data saved to {train_data_path}.")
        logging.info(f"Test data saved to {test_data_path}.")
        logging.info("Data ingestion completed successfully.")

    except Exception as e:
        logging.error(f"Error during data ingestion: {e}")
        raise
