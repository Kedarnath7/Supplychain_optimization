# Supply Chain Optimization

## 📌 Overview
This project focuses on optimizing the supply chain using **machine learning** and **automation**. It integrates **Apache Airflow** for workflow orchestration, **MLflow** for model monitoring, and **DVC** for data versioning. The project also leverages **Docker** for containerization and reproducibility.

## 🚀 Features
- **Automated Workflow Orchestration** using Apache Airflow
- **Machine Learning Model Monitoring** with MLflow & DagsHub
- **Data Versioning** with DVC
- **Containerized Environment** using Docker & Conda
- **Modular Architecture** with separate environments for main processing and orchestration

## 🛠️ Tech Stack
- **Programming Language**: Python
- **Workflow Orchestration**: Apache Airflow
- **Model Tracking**: MLflow
- **Data Versioning**: DVC
- **Containerization**: Docker
- **Virtual Environments**: Conda & venv
- **OS**: Linux

## 📂 Project Structure
```
📦 supply-chain-optimization
├── 📁 main            # Core ML & data processing files (Conda env)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── src
│   │   ├── data_preprocessing.py
│   │   ├── model_training.py
│   │   ├── evaluation.py
│   ├── config.yaml
├── 📁 airflow         # Workflow orchestration (Python venv)
│   ├── dags
│   │   ├── data_pipeline.py
│   │   ├── model_training_dag.py
│   ├── airflow.cfg
├── 📁 data            # Data files (tracked with DVC)
├── 📁 models          # Trained models (logged in MLflow)
├── README.md         # Project Documentation
```

## 🔧 Installation & Setup
### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/supply-chain-optimization.git
cd supply-chain-optimization
```

### 2️⃣ Set Up Conda Environment (Main)
```bash
conda create --name supply_chain python=3.8 -y
conda activate supply_chain
pip install -r main/requirements.txt
```

### 3️⃣ Set Up Airflow (Orchestration)
```bash
cd airflow
python -m venv airflow_env
source airflow_env/bin/activate
pip install apache-airflow
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

## 🛠️ To-Do & Future Enhancements
- [ ] Implement real-time data streaming
- [ ] Improve model retraining pipeline
- [ ] Add CI/CD automation for DAG triggers

## 🤝 Contribution
Feel free to fork this repository, submit issues, and contribute to improvements!

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Maintainer:** [Your Name](https://github.com/yourusername)
