
import sys
import os
from dataclasses import dataclass
from src.supply.logger import logging
from src.supply.exception import CustomException
from src.supply.components.data_ingestion import DataIngestion
from src.supply.components.data_ingestion import DataIngestionConfig
from src.supply.components.data_transformation import DataTransformation
from src.supply.components.model_trainer import ModelTrainer


class training_Pipeline:
    def __init__(self):
        self.ingestion = DataIngestion()
        self.transformation = DataTransformation()
        self.trainer = ModelTrainer()

    def execute_pipelines(self):
        try:

            train_path, test_path = self.ingestion.initiate_data_ingestion()

            tasks = [
                {
                    "task": "late_delivery_risk_prediction",
                    "numerical_col": ["Days_for_shipping_real", "Days_for_shipment_scheduled", "Product_Price", "Order_Item_Quantity", "Order_Item_Discount_Rate"],
                    "categorical_col": ["Shipping_Mode", "Category_Id", "Category_Name", "Order_State", "Order_Region","Order_Country"],
                    "target": "Late_delivery_risk",
                    "model_features": ["Category_Id", "Category_Name", "Days_for_shipping_real", "Days_for_shipment_scheduled", "Shipping_Mode", "Order_State", "Order_Region","Order_Country", "Product_Price", "Order_Item_Quantity", "Order_Item_Discount_Rate"],
                    "task_type": "classification",
                },
                {
                    "task": "order_profit_prediction",
                    "numerical_col": ['Sales', 'Product_Price', 'Order_Item_Quantity', 'Order_Item_Discount_Rate', 'Profit_Margin'],
                    "categorical_col": ['Shipping_Mode', 'Order_State', 'Order_Country', 'Customer_Segment'],
                    "target": "Order_Profit_Per_Order",
                    "model_features": ['Sales', 'Product_Price', 'Order_Item_Quantity', 'Order_Item_Discount_Rate', 'Profit_Margin', 
            'Shipping_Mode', 'Order_State', 'Order_Country', 'Customer_Segment'],
                    "task_type": "regression",
                },
                {
                    "task": "shipping_time_prediction",
                    "numerical_col": ["Days_for_shipment_scheduled", "Product_Price", "Order_Item_Quantity","Order_Item_Discount_Rate"],
                    "categorical_col": ["Shipping_Mode", "Category_Id", "Category_Name", "Order_State", "Order_Region","Order_Country"],
                    "target": "Days_for_shipping_real",
                    "model_features": ["Category_Id", "Category_Name", "Days_for_shipment_scheduled", "Shipping_Mode", "Order_State", "Order_Region","Order_Country", "Product_Price", "Order_Item_Quantity", "Order_Item_Discount_Rate"],
                    "task_type": "regression",
                }
            ]

            for task in tasks:
                logging.info(f"Starting pipeline for task: {task['task']}")

                features_config = {
                    task["target"]: {
                        "numerical": task['numerical_col'],
                        "categorical": task['categorical_col'],
                        "features": task['model_features']
                    }
                }

                transformed_data = self.transformation.initiate_data_transformation(train_path, test_path, features_config)
                

                score, model_path = self.trainer.train_model(
                    transformed_data[task["target"]],
                    target=task["target"],
                    task_type=task["task_type"]
                )
                logging.info(f"Task {task['task']} complete. Model saved at {model_path}. Performance_score: {score}")


        except Exception as e:
            raise CustomException(e, sys)
