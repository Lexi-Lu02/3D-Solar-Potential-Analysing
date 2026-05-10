"""Step 5: predict on 2023 buildings, optionally upsert to solar_score_v2.

Reads dataset_2023.parquet (built by build_features_2023.py from PG),
runs the LightGBM trained on 2015 features+labels, linearly maps 1–5 → 0–100,
writes per-structure_id rows to PG (no crosswalk needed — keys already align).
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore", message="X does not have valid feature names"
)

import joblib
import numpy as np
import pandas as pd

from _db import get_connection
from _preprocess import CATEGORICAL_FEATURES, NUMERIC_FEATURES  # noqa: F401

# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
ARTIFACTS = HERE / "artifacts"
DATASET_2023 = DATA_DIR / "dataset_2023.parquet"

PREDICTIONS_CSV = ARTIFACTS / "predictions_2023.csv"

# label scale clamps (1 = Very Poor, 5 = Excellent)
MIN_RAW = 1.0
MAX_RAW = 5.0
MODEL_NAME = "lgb"


def predict() -> pd.DataFrame:
    model_path = ARTIFACTS / f"{MODEL_NAME}.pkl"
    if not model_path.exists():
        sys.exit(f"[ERROR] {model_path} not found; run train.py first")
    if not DATASET_2023.exists():
        sys.exit(f"[ERROR] {DATASET_2023} not found; run build_features_2023.py")

    df = pd.read_parquet(DATASET_2023)
    n_total = len(df)
    print(f"[predict] {n_total} buildings in 2023 dataset")

    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    n_missing = df[NUMERIC_FEATURES].isna().any(axis=1).sum()
    if n_missing:
        print(f"  [info] {n_missing} rows had missing numeric features "
              f"(filled with median before predict)")
    df[NUMERIC_FEATURES] = df[NUMERIC_FEATURES].apply(
        lambda c: c.fillna(c.median()), axis=0
    )
    df[CATEGORICAL_FEATURES[0]] = df[CATEGORICAL_FEATURES[0]].fillna("UNKNOWN")

    pipe = joblib.load(model_path)
    raw_pred = pipe.predict(df[feature_cols])
    raw_pred = np.clip(raw_pred, MIN_RAW, MAX_RAW)
    score_0_100 = ((raw_pred - MIN_RAW) / (MAX_RAW - MIN_RAW) * 100.0).round().astype(int)

    out = pd.DataFrame({
        "structure_id": df["structure_id"].astype(int).to_numpy(),
        "lat": df["lat"].to_numpy(),
        "lng": df["lng"].to_numpy(),
        "suburb": df["suburb"].to_numpy(),
        "predicted_score_1_5": np.round(raw_pred, 3),
        "predicted_score_0_100": score_0_100,
        "model_version": MODEL_NAME,
    })
    out.to_csv(PREDICTIONS_CSV, index=False)
    print(f"  -> {PREDICTIONS_CSV}")

    print("\nscore distribution:")
    bin_edges = [-1, 20, 40, 60, 80, 100]
    bin_labels = ["VeryPoor (0-20)", "Poor (20-40)", "Moderate (40-60)",
                  "Good (60-80)", "Excellent (80-100)"]
    bins = pd.cut(out["predicted_score_0_100"], bins=bin_edges, labels=bin_labels)
    for label, count in bins.value_counts().sort_index().items():
        pct = 100 * count / len(out)
        print(f"  {label:<22} {count:>6}  ({pct:5.1f}%)")
    return out


def write_db(predictions: pd.DataFrame, model_version: str) -> None:
    print(f"\n[db] writing solar_score_v2 ...")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS solar_score_v2 (
            structure_id           INTEGER PRIMARY KEY,
            predicted_score_1_5    NUMERIC(4, 3),
            predicted_score_0_100  INTEGER CHECK (predicted_score_0_100 BETWEEN 0 AND 100),
            model_version          TEXT NOT NULL,
            computed_at            TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()

    # legacy schema (had structure_id_2023 / struct_id_2015 / had_label) → recreate
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='solar_score_v2'
    """)
    cols = {r[0] for r in cur.fetchall()}
    if "structure_id_2023" in cols:
        print("  [migrate] dropping old solar_score_v2 schema (had crosswalk fields)")
        cur.execute("DROP TABLE solar_score_v2")
        cur.execute("""
            CREATE TABLE solar_score_v2 (
                structure_id           INTEGER PRIMARY KEY,
                predicted_score_1_5    NUMERIC(4, 3),
                predicted_score_0_100  INTEGER CHECK (predicted_score_0_100 BETWEEN 0 AND 100),
                model_version          TEXT NOT NULL,
                computed_at            TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()

    import psycopg2.extras
    rows = [
        (
            int(r.structure_id),
            float(r.predicted_score_1_5),
            int(r.predicted_score_0_100),
            model_version,
        )
        for r in predictions.itertuples(index=False)
    ]
    psycopg2.extras.execute_batch(
        cur,
        """
        INSERT INTO solar_score_v2
            (structure_id, predicted_score_1_5, predicted_score_0_100, model_version)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (structure_id) DO UPDATE SET
            predicted_score_1_5   = EXCLUDED.predicted_score_1_5,
            predicted_score_0_100 = EXCLUDED.predicted_score_0_100,
            model_version         = EXCLUDED.model_version,
            computed_at           = NOW()
        """,
        rows,
        page_size=500,
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"  wrote {len(rows)} rows to solar_score_v2")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-db", action="store_true",
        help="upsert solar_score_v2 in PG (default: CSV only)",
    )
    args = parser.parse_args()

    print(f"=== Step 5: infer (model={MODEL_NAME}) ===\n")
    preds = predict()

    if args.write_db:
        write_db(preds, MODEL_NAME)
    else:
        print("\n[hint] DB write skipped; pass --write-db to upsert solar_score_v2")

    print("\ndone.")


if __name__ == "__main__":
    main()
