from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import json
import numpy as np
import joblib
import torch
import torch.nn as nn
from typing import Dict, Any
import logging
from collections import defaultdict
import time

# FastAPI app
app = FastAPI(title="Anomaly Detection API (Autoencoder)")

# Database
DB_PATH = "anomalies.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingest_time TEXT,
            is_anomaly INTEGER,
            score REAL,
            severity TEXT,
            raw TEXT
        )
    """)

    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_id ON anomalies(id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_time ON anomalies(ingest_time)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_severity ON anomalies(severity)")

    con.commit()
    con.close()


def optimize_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ingest_time ON anomalies(ingest_time)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_severity ON anomalies(severity)")
    con.commit()
    con.close()

init_db()
optimize_db()

# Alert config
CRITICAL_BURST_WINDOW_SEC = 60
CRITICAL_BURST_THRESHOLD = 5

HIGH_WINDOW_SEC = 60
HIGH_THRESHOLD = 3

critical_timestamps = []
high_tracker = defaultdict(list)

# Alert logger
logging.basicConfig(
    filename="alerts.log",
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def send_alert(severity: str, score: float, srcip: str | None):
    msg = f"[{severity}] score={score:.6f} srcip={srcip}"
    print("🚨 ALERT:", msg)

    if "CRITICAL" in severity:
        logging.critical(msg)
    else:
        logging.warning(msg)

# Severity logic
def severity_from_score(score: float) -> str:
    if score < 0.02:
        return "LOW"
    elif score < 0.1:
        return "MEDIUM"
    elif score < 1.0:
        return "HIGH"
    else:
        return "CRITICAL"

# Autoencoder model
class AutoEncoder(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
        )
        self.decoder = nn.Sequential(
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

with open("models/ae_features.json", "r") as f:
    AE_FEATURES = json.load(f)

AE_SCALER = joblib.load("models/ae_scaler.joblib")

AE_MODEL = AutoEncoder(len(AE_FEATURES))
AE_MODEL.load_state_dict(
    torch.load("models/autoencoder.pt", map_location=DEVICE)
)
AE_MODEL.to(DEVICE)
AE_MODEL.eval()

AE_THRESHOLD = 0.02

print(f"✅ Autoencoder loaded | device={DEVICE} | features={len(AE_FEATURES)}")


class IngestPayload(BaseModel):
    data: Dict[str, Any]

def compute_reconstruction_error(row: dict) -> float:
    try:
        values = []
        for f in AE_FEATURES:
            try:
                values.append(float(row.get(f, 0.0)))
            except Exception:
                values.append(0.0)

        x = np.array(values, dtype=np.float32).reshape(1, -1)
        x_scaled = AE_SCALER.transform(x)
        x_tensor = torch.tensor(x_scaled).to(DEVICE)

        with torch.no_grad():
            recon = AE_MODEL(x_tensor)

        return torch.mean((x_tensor - recon) ** 2).item()

    except Exception as e:
        print("AE error:", e)
        return 0.0

# API: INGEST
@app.post("/ingest")
def ingest(payload: IngestPayload):
    score = compute_reconstruction_error(payload.data)
    is_anomaly = int(score > AE_THRESHOLD)
    severity = severity_from_score(score)

    srcip = (
        payload.data.get("srcip")
        or payload.data.get("r_srcip")
        or payload.data.get("col_0")
    )

    now = time.time()

    # ALERT LOGIC 
    global critical_timestamps

    if severity == "CRITICAL":
        send_alert(severity, score, srcip)
        critical_timestamps.append(now)
        critical_timestamps = [
            t for t in critical_timestamps
            if now - t <= CRITICAL_BURST_WINDOW_SEC
        ]

    elif severity == "HIGH" and srcip:
        high_tracker[srcip].append(now)
        high_tracker[srcip] = [
            t for t in high_tracker[srcip]
            if now - t <= HIGH_WINDOW_SEC
        ]

        if len(high_tracker[srcip]) >= HIGH_THRESHOLD:
            send_alert("HIGH (REPEATED)", score, srcip)
            high_tracker[srcip].clear()

    # STORE
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO anomalies (ingest_time, is_anomaly, score, severity, raw)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            is_anomaly,
            score,
            severity,
            json.dumps(payload.data),
        ),
    )
    con.commit()
    con.close()

    return {
        "is_anomaly": is_anomaly,
        "score": score,
        "severity": severity,
    }

@app.get("/alerts")
def alerts():
    now = time.time()
    recent_critical = [
        t for t in critical_timestamps
        if now - t <= CRITICAL_BURST_WINDOW_SEC
    ]

    active = []
    if len(recent_critical) >= CRITICAL_BURST_THRESHOLD:
        active.append({
            "type": "CRITICAL_BURST",
            "level": "CRITICAL",
            "message": f"{len(recent_critical)} CRITICAL anomalies in last 60s"
        })

    return {
        "active_alerts": active,
        "critical_last_minute": len(recent_critical)
    }

# API: FETCH ANOMALIES
@app.get("/anomalies")
def get_anomalies(limit: int = 300):
    con = sqlite3.connect(DB_PATH, timeout=10)
    cur = con.cursor()

    cur.execute("""
        SELECT id, ingest_time, score, severity, raw
        FROM anomalies
        WHERE is_anomaly = 1
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    con.close()

    return {
        "anomalies": [
            {
                "id": r[0],
                "ingest_time": r[1],
                "score": r[2],
                "severity": r[3],
                "raw": r[4]
            }
            for r in rows
        ]
    }


# API: SINGLE ANOMALY
@app.get("/anomalies/{anomaly_id}")
def get_anomaly(anomaly_id: int):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT raw FROM anomalies WHERE id = ?", (anomaly_id,))
    row = cur.fetchone()
    con.close()

    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    return {"raw": row[0]}

@app.get("/alerts")
def get_alerts(limit: int = 100):
    alerts = []

    try:
        with open("alerts.log", "r") as f:
            lines = f.readlines()[-limit:]

        for line in lines:
            alerts.append(line.strip())

    except FileNotFoundError:
        pass

    return {"alerts": alerts}

# API: MODEL INFO
@app.get("/model_info")
def model_info():
    return {
        "model_type": "autoencoder",
        "device": DEVICE,
        "feature_count": len(AE_FEATURES),
        "threshold": AE_THRESHOLD,
    }
