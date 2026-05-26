# 🚨 Real-Time Network Anomaly Detection & Monitoring System

A production-style AI-powered cybersecurity monitoring platform that detects anomalous network behavior in real time using a deep learning autoencoder, classifies threat severity, stores live anomaly events, and visualizes insights through an interactive analytics dashboard.

Built with:

* PyTorch → Deep Learning Autoencoder
* FastAPI → Real-Time Inference API
* SQLite → Persistent Anomaly Storage
* Streamlit → Interactive Monitoring Dashboard
* Docker + Render + Streamlit Cloud → Cloud Deployment

---

# 📌 Project Overview

Traditional monitoring systems struggle to detect unknown or evolving threats in dynamic network environments.

This project solves that problem using:

* Unsupervised Deep Learning
* Real-Time Inference
* Live Threat Visualization
* Severity-Based Alerting
* Interactive Security Analytics

The system continuously ingests network traffic data, reconstructs normal patterns using an autoencoder neural network, and flags high reconstruction-error samples as anomalies.

---

# 🧠 Core Idea

The autoencoder is trained only on normal traffic patterns.

When abnormal traffic appears:

```text
Input ≠ Reconstructed Output
```

The reconstruction error increases.

If the error crosses a threshold:

```text
Anomaly Detected
```

---

# ✨ Features

## AI-Powered Detection

* Autoencoder-based anomaly detection
* Unsupervised learning approach
* Reconstruction error scoring

## Real-Time Monitoring

* Continuous data ingestion
* Live FastAPI inference pipeline
* Real-time dashboard updates

## Threat Classification

Severity levels:

* LOW
* MEDIUM
* HIGH
* CRITICAL

## Interactive Analytics Dashboard

Includes:

* Time-series anomaly trends
* Severity distribution donut chart
* Per-IP anomaly timelines
* Top offending source IPs
* Live anomaly tables
* Interactive filtering controls

## Persistent Storage

* SQLite-based anomaly database
* Historical anomaly tracking
* Exportable records

## Alerting System

* Real-time security alerts
* Critical anomaly notifications
* Persistent logging

## Cloud Deployment

* Backend deployed on Render
* Dashboard deployed on Streamlit Cloud
* GitHub-integrated deployment pipeline

---

# 🏗️ System Architecture

```text
                ┌─────────────────────┐
                │ Network Traffic Data │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Simulator / Ingest  │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ FastAPI Backend API │
                │  Real-Time Inference│
                └──────────┬──────────┘
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐
│ SQLite Database  │             │ Alert Logging    │
│ anomalies.db     │             │ alerts.log       │
└──────────────────┘             └──────────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Streamlit Dashboard │
                │ Monitoring & Charts │
                └─────────────────────┘
```

---

# 📂 Project Structure

```text
anomaly-detection/
│
├── app_improved.py               # FastAPI backend API
├── dashboard_enhanced_v2.py      # Streamlit dashboard
├── simulator.py                  # Real-time anomaly simulator
├── train_autoencoder.py          # Autoencoder training pipeline
├── subset_generator.py           # Dataset preprocessing
│
├── data/
│   └── subsetA.csv               # Demo dataset subset
│
├── models/
│   ├── autoencoder.pt            # Trained PyTorch model
│   ├── ae_scaler.joblib          # Feature scaler
│   └── ae_features.json          # Feature definitions
│
├── anomalies.db                  # SQLite anomaly database
├── alerts.log                    # Security alert logs
├── requirements.txt
├── Dockerfile
├── .gitignore
└── README.md
```

---

# 🧱 Tech Stack

| Layer              | Technology              |
| ------------------ | ----------------------- |
| Deep Learning      | PyTorch                 |
| Backend API        | FastAPI                 |
| Frontend Dashboard | Streamlit               |
| Database           | SQLite                  |
| Data Processing    | Pandas, NumPy           |
| Visualization      | Plotly                  |
| Deployment         | Render, Streamlit Cloud |
| Model Storage      | Joblib, JSON            |
| Language           | Python                  |

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/rajesh-9553/anomaly-detection.git
cd anomaly-detection
```

## Create Virtual Environment

### Windows

```bash
python -m venv anomaly
anomaly\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv anomaly
source anomaly/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Project

## Start FastAPI Backend

```bash
python -m uvicorn app_improved:app --reload --port 8000
```

API Documentation:

```text
http://localhost:8000/docs
```

## Start Streamlit Dashboard

```bash
streamlit run dashboard_enhanced_v2.py
```

Dashboard URL:

```text
http://localhost:8501
```

## Start Real-Time Simulator

```bash
python simulator.py
```

This continuously streams network records to the backend API for real-time inference and visualization.

---

# 📊 Dashboard Capabilities

The dashboard provides:

* Real-time anomaly monitoring
* Threat severity visualization
* Top suspicious IP analysis
* Interactive filtering
* Historical anomaly tracking
* Security alerting
* Per-IP timeline analysis

---

# 🧠 Autoencoder Workflow

```text
Input Features
      │
      ▼
 Encoder Compresses Data
      │
      ▼
 Bottleneck Representation
      │
      ▼
 Decoder Reconstructs Input
      │
      ▼
Reconstruction Error Calculated
      │
      ▼
Threshold Comparison
      │
      ▼
Anomaly Classification
```

---

# 📁 Dataset Information

This project uses the UNSW-NB15 cybersecurity dataset.

Due to GitHub file-size limitations, only a small working subset is included.

## Included

```text
subsetA.csv
```

## Excluded

```text
UNSW-NB15_1.csv
UNSW-NB15_2.csv
```

Dataset Source:

```text
https://research.unsw.edu.au/projects/unsw-nb15-dataset
```

---

# ☁️ Deployment

## Backend

Deployed on Render using Docker containerization.

## Dashboard

Deployed on Streamlit Cloud.

## Deployment Workflow

```text
Git Push → Auto Deploy → Live Dashboard Update
```

---

# 🔮 Future Improvements

* WebSocket-based live streaming
* Kafka event pipeline
* PostgreSQL integration
* Grafana observability
* Kubernetes orchestration
* LLM-powered anomaly explanation
* Multi-model ensemble detection

---

# 👨‍💻 Author

## Rajesh S

Artificial Intelligence & Machine Learning

Built as a real-time AI engineering and cybersecurity monitoring project demonstrating:

* Deep Learning
* Real-Time Inference
* Full-Stack AI Deployment
* Monitoring Systems
* Interactive Visualization

---

# ⭐ Final Note

This project is not just a machine learning model — it is a complete real-time AI monitoring pipeline simulating how modern anomaly detection systems are designed, deployed, monitored, and visualized in production environments.
