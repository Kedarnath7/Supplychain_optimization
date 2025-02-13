
import pandas as pd
import pickle

def load_pickle(file_path):
    with open(file_path, 'rb') as f:
        return  pickle.load(f)
    
def preprocess_and_predict(input_csv_path, output_csv_path):
    df = pd.read_csv(input_csv_path)

    preprocessors = {
        "late_delivery_risk": load_pickle("artifacts/Late_delivery_risk_preprocessor.pkl"),
        "order_profit": load_pickle("artifacts/Order_Profit_Per_Order_preprocessor.pkl"),
        "shipping_time": load_pickle("artifacts/Days_for_shipping_real_preprocessor.pkl"),
    }
    models = {
        "late_delivery_risk": load_pickle("artifacts/models/Late_delivery_risk_model.pkl"),
        "order_profit": load_pickle("artifacts/models/Order_Profit_Per_Order_model.pkl"),
        "shipping_time": load_pickle("artifacts/models/Days_for_shipping_real_model.pkl"),
    }

    tasks = [
        {
            "name": "Late_Delivery_Risk",
            "features": ["Days_for_shipping_real", "Days_for_shipment_scheduled", "Product_Price", 
                         "Order_Item_Quantity", "Order_Item_Discount_Rate", "Shipping_Mode", 
                         "Category_Id", "Category_Name", "Order_State", "Order_Region", "Order_Country"],
            "preprocessor": "late_delivery_risk",
            "model": "late_delivery_risk",
            "postprocess": lambda x: ["Delivery on Time" if i == 0 else "Late Delivery" for i in x]  
        },
        {
            "name": "Order_Profit",
            "features": ['Sales', 'Product_Price', 'Order_Item_Quantity', 'Order_Item_Discount_Rate', 
                         'Profit_Margin', 'Shipping_Mode', 'Order_State', 'Order_Country', 'Customer_Segment'],
            "preprocessor": "order_profit",
            "model": "order_profit"
        },
        {
            "name": "Shipping_Time",
            "features": ["Days_for_shipment_scheduled", "Product_Price", "Order_Item_Quantity", 
                         "Order_Item_Discount_Rate", "Shipping_Mode", "Category_Id", "Category_Name", 
                         "Order_State", "Order_Region", "Order_Country"],
            "preprocessor": "shipping_time",
            "model": "shipping_time",
            "postprocess": lambda x: [round(i) for i in x]  
        }
    ]

    output_df = df[["Order_Id", "Product_Name"]].copy()

    for task in tasks:
        features = df[task["features"]]

        preprocessor = preprocessors[task["preprocessor"]]
        transformed_data = preprocessor.transform(features)

        model = models[task["model"]]
        predictions = model.predict(transformed_data)

        if 'postprocess' in task:
            predictions = task["postprocess"](predictions)

        output_df[task["name"]] = predictions

    output_df.to_csv(output_csv_path, index=False)
