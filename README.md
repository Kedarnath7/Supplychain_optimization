# Supply Chain Optimization

## 📌 Overview
This project focuses on optimizing the supply chain using **machine learning algotithms** and **automation**. It integrates **Apache Airflow** for workflow orchestration, **MLflow** for model monitoring, and **DVC** for data versioning. The project also leverages **Docker** for containerization and reproducibility.

## 🚀 Features
- **Automated Workflow Orchestration** using Apache Airflow
- **Machine Learning Model Monitoring** with MLflow & DagsHub
- **Data Versioning** with DVC
- **Containerized Environment** using Docker & Conda
- **Modular Architecture** with separate environments for main processing and orchestration

## 📂 Project Structure
```
📦 supply-chain-optimization
├── 📁 main            # Core ML & data processing files (Conda env)
│   ├── src/supply
│   │   ├── components
│   │   │   ├── data_ingestion.py
│   │   │   ├── data_transformation.py
│   │   │   ├── model_training.py
│   │   ├── pipelines
│   │   │   ├── prediction_pipeline.py
│   │   │   ├── training_pipeline.py
│   │   ├── __init__.py
│   │   ├── exception.py
│   │   ├── logger.py
│   │   ├── utils.py
│   ├── templates
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
├── 📁 airflow         # Workflow orchestration (Python venv)
│   ├── dags
│   │   ├── modular_dag.py
│   │   ├── supplychain_dag.py
│   ├── src
│   │   ├── config
│   │   ├── __init__.py
│   │   ├── data_ingestion.py
│   │   ├── data_transformation.py
│   │   ├── load_to_postgres.py
│   │   ├── model_training.py
│   │   ├── read_mysql_data.py
│   ├── airflow.cfg
├── 📁 main/artifacts            # Data files (tracked with DVC) and models
├── 📁 aiflow/artifacts          # Airflow Data files (tracked with DVC) and models
├── README.md         # Project Documentation
```

## 🔧 Installation & Setup
### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Kedarnath7/Supplychain_optimization.git
cd main
```

### 2️⃣ Set Up Conda Environment (Main)
```bash
conda create --name venv python=3.8 -y
conda activate venv
pip install -r main/requirements.txt
```

### 3️⃣ Set Up Airflow (Orchestration)
```bash
cd airflow
python -m venv airflow-venv
source airflow-venv/bin/activate
pip install apache-airflow
pip install -r airflow/requirements.txt #or use sudo
```

### 4️⃣ Run Docker for Containerization (Optional)
```bash
cd main
docker build -t supply-chain-optimization .
docker run -p 5000:5000 supply-chain-optimization
```

### 5️⃣ Start Airflow Scheduler & Webserver
```bash
airflow scheduler &
airflow webserver -p 8080 &
```

## 🚦 Usage
- **Trigger Airflow DAGs**: Open [Airflow UI](http://localhost:8080) and start the pipeline.
- **Monitor ML Models**: Open [DagsHub](https://dagshub.com/) or MLflow UI. 
- **Manage Data Versions**: Use DVC commands like `dvc pull` & `dvc push`.

## 📊 Output & Results
- The system processes real-time and historical supply chain data to optimize routes and inventory.
- **Visualization**: The results are displayed in interactive dashboards using **Matplotlib, Seaborn, and Plotly**.
- **Model Insights**: MLflow tracks model performance, including accuracy, loss metrics, and parameter tuning.
- **Orchestration Logs**: Apache Airflow logs workflow execution, failures, and success reports.
- **Data Version Control**: DVC ensures versioned datasets, enabling reproducible experiments.
- **DagsHub**: View and monitor your data, models, and experiments on [DagsHub](https://dagshub.com/kedarnathpinjala11/Supplychain_optimization).

## 🛠️ To-Do & Future Enhancements
- [ ] Implement real-time data streaming
- [ ] Improve model retraining pipeline
- [ ] Add CI/CD automation for DAG triggers

## 🤝 Contribution
Feel free to fork this repository, submit issues, and contribute to improvements!

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Maintainer:** [Kedarnath](https://github.com/Kedarnath7)
