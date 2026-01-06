# 🚨 Anomaly Detection Dashboard (Interactive)

A real-time **network anomaly detection platform** built using **deep learning autoencoders**, designed to detect suspicious behavior, classify severity, and visualize threats through an interactive dashboard.

This project demonstrates **end-to-end AI engineering**, including model training, real-time inference, alerting, storage, and visualization.

---

## 📌 Overview

This system ingests network traffic data, detects anomalous patterns using an **unsupervised autoencoder**, assigns severity levels, and presents insights via a **live dashboard**.

It closely mirrors how **production-grade AI monitoring systems** are built in cybersecurity environments.

---

## ✨ Key Features

- 🔍 Autoencoder-based anomaly detection (unsupervised)
- ⚡ Real-time ingestion & inference using FastAPI
- 🚦 Severity classification (LOW, MEDIUM, HIGH, CRITICAL)
- 🧠 Deep learning model built with PyTorch
- 💾 Persistent storage using SQLite
- 🚨 Alert generation & logging
- 📊 Interactive Streamlit dashboard
- 📈 Time-series & per-IP anomaly visualization
- 🍩 Severity distribution donut chart
- 📤 Exportable anomaly records (CSV)
- 🧩 Modular & reproducible project structure

---

## 🧱 System Architecture

```text
Network Traffic (CSV / Stream)
            |
            v
     Simulator / Ingest Client
            |
            v
        FastAPI Backend
     (Autoencoder Inference)
            |
            +--> SQLite Database (anomalies.db)
            |
            +--> Alert Logs (alerts.log)
            |
            v
     Streamlit Dashboard
   (Monitoring & Visualization)


Project Structure

anomaly-detection/
│
├── app_improved.py              # FastAPI backend
├── dashboard_enhanced_v2.py     # Streamlit dashboard
├── simulator.py                 # Real-time data simulator
├── train_autoencoder.py         # Model training script
├── subset_generator.py          # Dataset preprocessing
│
├── data/
│   └── subsetA.csv              # Small working dataset
│
├── models/
│   ├── autoencoder.pt
│   ├── ae_scaler.joblib
│   └── ae_features.json
│
├── anomalies.db                 # SQLite anomaly storage
├── alerts.log                   # Alert logs
├── requirements.txt
├── .gitignore
└── README.md


🚀 Installation

1️⃣ Clone the Repository
git clone https://github.com/rajesh-9553/anomaly-detection.git
cd anomaly-detection

2️⃣ Create & Activate Virtual Environment
python -m venv anomaly

Windows
anomaly\Scripts\activate

Linux / macOS
source anomaly/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt

▶️ Running the Project
🔹 Start FastAPI Backend
python -m uvicorn app_improved:app --reload --port 8000


API Docs:
http://localhost:8000/docs

🔹 Start Streamlit Dashboard
streamlit run dashboard_enhanced_v2.py


Dashboard:
http://localhost:8501

🔹 Start Data Simulator (Optional)
python simulator.py

This streams data continuously to the API.

📁 Dataset Information

This project uses the UNSW-NB15 dataset.
Due to GitHub size limits, full datasets are not included.

Included:
subsetA.csv (demo subset)

Excluded:
UNSW-NB15_1.csv
UNSW-NB15_2.csv

Dataset source:
https://research.unsw.edu.au/projects/unsw-nb15-dataset















