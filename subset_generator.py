import os
import pandas as pd
import random
import csv
from pathlib import Path

DATA_DIR = Path("data")
OUT_FILE = DATA_DIR / "subsetA.csv"

# Desired counts
NORMAL_SAMPLES = 20000
ATTACK_SAMPLES = 30000

# CSV chunk size - tune for memory
CHUNKSIZE = 100_000

# Possible label column names in UNSW-like datasets
LABEL_COL_CANDIDATES = ["label", "attack", "attack_cat", "is_attack"]

random.seed(42)

def file_has_header(path, n_check=5):
    """
    Peek first n_check rows and decide if the first row is header.
    Heuristic: if first row contains any non-numeric value that matches common header names,
    or many alphabetic strings (like 'srcip' or 'proto'), we treat it as header.
    """
    import csv
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        rows = []
        for i, r in enumerate(reader):
            rows.append(r)
            if i >= n_check - 1:
                break
    if not rows:
        return False
    first = rows[0]
    # if any of the label candidates appear in row0 -> header
    row0_lower = [str(x).strip().lower() for x in first]
    for cand in LABEL_COL_CANDIDATES:
        if cand in row0_lower:
            return True
    # if majority of first row items are alphabetic-ish (contain letters and non-numeric) -> header
    alpha_count = 0
    for v in first:
        s = str(v).strip()
        # treat IPv4-looking values (contains '.') as numeric-like for our heuristic
        if any(c.isalpha() for c in s) and not any(c.isdigit() for c in s):
            alpha_count += 1
    if alpha_count >= max(1, len(first)//3):
        return True
    return False

def detect_label_column_from_header(sample_df):
    """Return best guess for label column name from a small DataFrame sample."""
    for cand in LABEL_COL_CANDIDATES:
        if cand in sample_df.columns:
            return cand
    cols = sample_df.columns.tolist()
    last_col = cols[-1]
    try:
        vals = sample_df[last_col].dropna().astype(str).str.strip().unique()[:10]
        if any(v in ("0","1","normal","benign") for v in (str(x).lower() for x in vals)):
            return last_col
    except Exception:
        pass
    return None

def is_attack_row(row, label_col):
    """Return True if row is an attack according to column semantics."""
    val = row.get(label_col)
    if val is None:
        return False
    try:
        v = float(val)
        return v != 0.0
    except Exception:
        s = str(val).strip().lower()
        if s in ("normal", "benign", "normal traffic", "none", ""):
            return False
        return True

def reservoir_sample_update(reservoir, k, item, seen_count):
    if len(reservoir) < k:
        reservoir.append(item)
    else:
        j = random.randrange(seen_count)
        if j < k:
            reservoir[j] = item

def process_files(data_dir, normal_k, attack_k, chunksize=100_000):
    csv_files = sorted([p for p in data_dir.glob("*.csv") if p.is_file()])
    if not csv_files:
        raise SystemExit(f"No CSV files found in {data_dir}. Place UNSW CSV(s) there.")

    print("Found CSV files:", csv_files)
    first_file = csv_files[0]
    header_present = file_has_header(first_file)
    print(f"Header detected in {first_file}: {header_present}")

    label_col = None
    if header_present:
        sample = pd.read_csv(first_file, nrows=500)
        label_col = detect_label_column_from_header(sample)
        if label_col is None:
            print("Warning: couldn't auto-detect label name from header. Will attempt last-column heuristics.")
    else:
        print("No header detected. We'll treat files as headerless and assume label is the last column.")

    normal_res = []
    attack_res = []
    seen_normal = 0
    seen_attack = 0

    for p in csv_files:
        print("Processing", p)
        if header_present:
            reader = pd.read_csv(p, chunksize=chunksize)
            for chunk in reader:
                if label_col is None:
                    label_col = detect_label_column_from_header(chunk)
                    if label_col:
                        print("Detected label column:", label_col)
                for _, row in chunk.iterrows():
                    rowd = row.to_dict()
                    if label_col is None:
                        label_col_candidate = list(rowd.keys())[-1]
                        if is_attack_row(rowd, label_col_candidate):
                            seen_attack += 1
                            if seen_attack <= attack_k:
                                attack_res.append(rowd)
                            else:
                                reservoir_sample_update(attack_res, attack_k, rowd, seen_attack)
                        else:
                            seen_normal += 1
                            if seen_normal <= normal_k:
                                normal_res.append(rowd)
                            else:
                                reservoir_sample_update(normal_res, normal_k, rowd, seen_normal)
                    else:
                        if is_attack_row(rowd, label_col):
                            seen_attack += 1
                            if seen_attack <= attack_k:
                                attack_res.append(rowd)
                            else:
                                reservoir_sample_update(attack_res, attack_k, rowd, seen_attack)
                        else:
                            seen_normal += 1
                            if seen_normal <= normal_k:
                                normal_res.append(rowd)
                            else:
                                reservoir_sample_update(normal_res, normal_k, rowd, seen_normal)
        else:
            for chunk in pd.read_csv(p, header=None, chunksize=chunksize):
                chunk.columns = [f"col_{i}" for i in range(chunk.shape[1])]
                label_col_candidate = chunk.columns[-1] 
                for _, row in chunk.iterrows():
                    rowd = row.to_dict()
                    if is_attack_row(rowd, label_col_candidate):
                        seen_attack += 1
                        if seen_attack <= attack_k:
                            attack_res.append(rowd)
                        else:
                            reservoir_sample_update(attack_res, attack_k, rowd, seen_attack)
                    else:
                        seen_normal += 1
                        if seen_normal <= normal_k:
                            normal_res.append(rowd)
                        else:
                            reservoir_sample_update(normal_res, normal_k, rowd, seen_normal)

    print(f"Seen normal rows: {seen_normal}, collected: {len(normal_res)}")
    print(f"Seen attack rows: {seen_attack}, collected: {len(attack_res)}")

    combined = normal_res + attack_res
    random.shuffle(combined)

    if not combined:
        raise SystemExit("No rows sampled. Check CSVs and label detection.")

    all_keys = set()
    for r in combined:
        all_keys.update(r.keys())
    cols = list(all_keys)
    for cand in LABEL_COL_CANDIDATES[::-1]:
        if cand in cols:
            cols.remove(cand)
            cols = [cand] + cols
            break

    print("Writing", OUT_FILE, "with", len(combined), "rows")
    with OUT_FILE.open("w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        writer.writeheader()
        for row in combined:
            writer.writerow({k: row.get(k, "") for k in cols})

    print("Done. Subset saved to", OUT_FILE)
    return OUT_FILE

if __name__ == "__main__":
    out = process_files(DATA_DIR, NORMAL_SAMPLES, ATTACK_SAMPLES, CHUNKSIZE)
