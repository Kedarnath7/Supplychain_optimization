from flask import Flask, request, render_template
import os
import pandas as pd
import plotly.express as px
from src.supply.pipelines.prediction_pipeline import preprocess_and_predict

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('upload.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return render_template('upload.html', message="No file uploaded!")
    file = request.files['file']
    if file.filename == '':
        return render_template('upload.html', message="No selected file!")

    input_csv_path = os.path.join("temp", "uploaded_input.csv")
    os.makedirs(os.path.dirname(input_csv_path), exist_ok=True)
    file.save(input_csv_path)

    output_csv_path = os.path.join("temp", "output_predictions.csv")
    preprocess_and_predict(input_csv_path, output_csv_path)
    output_df = pd.read_csv(output_csv_path)

    return render_template('result.html', table_data=output_df.to_dict(orient='records'),
                           columns=output_df.columns.tolist())

@app.route('/visualize')
def visualize():
    input_csv_path = os.path.join("temp", "uploaded_input.csv")
    output_csv_path = os.path.join("temp", "output_predictions.csv")

    if not os.path.exists(input_csv_path) or not os.path.exists(output_csv_path):
        return render_template('visualize.html', message="Required files are missing! Please upload a file first.")

    input_df = pd.read_csv(input_csv_path)
    output_df = pd.read_csv(output_csv_path)

    if 'Late_Delivery_Risk' not in output_df.columns or 'Order_Profit' not in output_df.columns:
        return render_template('visualize.html', message="Required columns are missing in output dataset!")

    delivery_pie = px.pie(output_df, names='Late_Delivery_Risk', title='Delivery Predictions (Late vs On Time)')
    delivery_pie_html = delivery_pie.to_html(full_html=False)

    merged_df = pd.merge(output_df, input_df[['Order_Id', 'Order_Region']], on='Order_Id', how='inner')

    profit_by_region = merged_df.groupby('Order_Region')['Order_Profit'].sum().reset_index()

    profit_bar = px.bar(profit_by_region, x='Order_Region', y='Order_Profit',
                        title='Total Profit Distribution by Region',
                        labels={'Order_Region': 'Region', 'Order_Profit': 'Total Profit'})
    profit_bar_html = profit_bar.to_html(full_html=False)

    late_deliveries = output_df[output_df['Late_Delivery_Risk'] == 'Late Delivery']
    late_deliveries = late_deliveries[['Order_Id']]
    late_deliveries = pd.merge(late_deliveries, input_df[['Order_Id', 'Customer_Country', 'Customer_City']], on='Order_Id', how='inner')
    late_deliveries = late_deliveries.drop_duplicates()

    if late_deliveries.empty:
        late_deliveries_html = "<p>No late deliveries found!</p>"
    else:
        late_deliveries_html = late_deliveries.to_html(classes="table table-striped", index=False)

    return render_template(
        'visualize.html',
        delivery_pie=delivery_pie_html,
        profit_bar=profit_bar_html,
        late_deliveries_table=late_deliveries_html
    )

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')