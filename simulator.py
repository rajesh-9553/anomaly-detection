import time
import requests
import csv
import random
from pathlib import Path

API_URL = "http://localhost:8000/ingest"
SUBSET = Path("data/subsetA.csv")
DELAY = 0.1

def row_to_event(header, row):
    d = {h: v for h, v in zip(header, row)}
    if "timestamp" not in d:
        d["timestamp"] = ""
    return d

def main():
    if not SUBSET.exists():
        print("subset not found:", SUBSET)
        return

    with SUBSET.open("r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    print("Loaded rows:", len(rows), "— streaming to", API_URL)
    random.shuffle(rows)

    for idx, row in enumerate(rows):
        event = row_to_event(header, row) 

        try:
            r = requests.post(
                API_URL,
                json={"data": event},
                timeout=15
            )

            if r.status_code == 200:
                out = r.json()
                if out.get("is_anomaly", 0) == 1:
                    print(f"[{idx}] ANOMALY score={out.get('score'):.4f}")
            else:
                print("HTTP", r.status_code, r.text)

        except Exception as e:
            print("Request error:", e)

        time.sleep(DELAY)

if __name__ == "__main__":
    main()
