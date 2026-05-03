"""
Step 5: 推理 + 2015→2023 ID 交叉映射 + 写库 (solar_score_v2)。

- 读 dataset_2015_full.parquet (含所有 2015 footprint, 标签可能为 NaN)
- 用 artifacts/xgb.pkl 预测 1–5
- (pred-1)/4*100 线性映 0–100, 与 Backend 现有显示一致
- 用 Data wrangling/buildings.csv 中的 2023 structure_id + lat/lng 做
  KD-Tree 最近邻, 建立 2015 struct_id → 2023 structure_id 映射
- 默认仅落盘 CSV; 加 --write-db 才连接 PostgreSQL 写表 solar_score_v2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from _preprocess import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET  # noqa: F401

# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
ARTIFACTS = HERE / "artifacts"
DATASET_FULL = DATA_DIR / "dataset_2015_full.parquet"

BUILDINGS_2023_CSV = (
    HERE.parent / "Data wrangling" / "buildings.csv"
)

PREDICTIONS_CSV = ARTIFACTS / "predictions_2015.csv"
CROSSWALK_CSV = ARTIFACTS / "id_crosswalk_2015_to_2023.csv"
JOINED_CSV = ARTIFACTS / "predictions_with_2023_id.csv"

# 与 Backend/app/services/building_query.py 现有映射一致
MIN_RAW = 1.0
MAX_RAW = 5.0


# ---------------------------------------------------------------------------
MODEL_NAME = "xgb"


def predict() -> pd.DataFrame:
    model_path = ARTIFACTS / f"{MODEL_NAME}.pkl"
    if not model_path.exists():
        sys.exit(f"[ERROR] {model_path} not found; run train.py first")
    if not DATASET_FULL.exists():
        sys.exit(f"[ERROR] {DATASET_FULL} not found; run build_features.py")

    df = pd.read_parquet(DATASET_FULL)
    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    # 缺失值最简单处理: 数值列用中位数, suburb 用 'UNKNOWN'
    n_missing_numeric = df[NUMERIC_FEATURES].isna().any(axis=1).sum()
    df[NUMERIC_FEATURES] = df[NUMERIC_FEATURES].apply(
        lambda c: c.fillna(c.median()), axis=0
    )
    df[CATEGORICAL_FEATURES[0]] = df[CATEGORICAL_FEATURES[0]].fillna("UNKNOWN")

    pipe = joblib.load(model_path)
    raw = pipe.predict(df[feature_cols])
    # 钳到 [1,5] 防止外推超界
    raw = np.clip(raw, MIN_RAW, MAX_RAW)
    score_0_100 = ((raw - MIN_RAW) / (MAX_RAW - MIN_RAW) * 100.0).round().astype(int)

    out = pd.DataFrame({
        "struct_id_2015": df["struct_id"].astype(int),
        "lat": df["lat"],
        "lng": df["lng"],
        "predicted_score_1_5": np.round(raw, 3),
        "predicted_score_0_100": score_0_100,
        "had_label": df["solar_score_avg"].notna(),
        "expert_score_1_5": df["solar_score_avg"],
        "model_version": MODEL_NAME,
    })
    print(f"[predict] {len(out)} buildings; "
          f"{n_missing_numeric} had missing numeric features (filled with median)")
    out.to_csv(PREDICTIONS_CSV, index=False)
    print(f"  -> {PREDICTIONS_CSV}")
    return out


# ---------------------------------------------------------------------------
def build_crosswalk(predictions: pd.DataFrame) -> pd.DataFrame:
    if not BUILDINGS_2023_CSV.exists():
        sys.exit(f"[ERROR] {BUILDINGS_2023_CSV} not found")

    print(f"[crosswalk] loading 2023 buildings from {BUILDINGS_2023_CSV.name} ...")
    b23 = pd.read_csv(
        BUILDINGS_2023_CSV,
        usecols=["structure_id", "lat", "lng"],
    )
    print(f"  {len(b23)} 2023 buildings")

    tree = cKDTree(b23[["lat", "lng"]].to_numpy())
    dist, nn = tree.query(predictions[["lat", "lng"]].to_numpy(), k=1)

    cross = pd.DataFrame({
        "struct_id_2015": predictions["struct_id_2015"].to_numpy(),
        "structure_id_2023": b23["structure_id"].to_numpy()[nn],
        "match_distance_deg": dist,  # 单位是经纬度度数
    })
    # 经验阈值仅用于打印诊断, 不影响数据
    far = (cross["match_distance_deg"] > 0.0005).sum()  # ≈ 50 m
    print(f"  matched; {far} pairs > ~50 m apart (worst-case fallback)")
    cross.to_csv(CROSSWALK_CSV, index=False)
    print(f"  -> {CROSSWALK_CSV}")
    return cross


def join_predictions_with_crosswalk(
    predictions: pd.DataFrame, cross: pd.DataFrame
) -> pd.DataFrame:
    # 一个 2023 building 可能被多个 2015 building 映到; 取分数最高 (避免大楼被某个小棚屋覆盖)
    j = predictions.merge(cross, on="struct_id_2015", how="inner")
    j = j.sort_values("predicted_score_1_5", ascending=False)
    j = j.drop_duplicates("structure_id_2023", keep="first")
    j.to_csv(JOINED_CSV, index=False)
    print(f"[join] {len(j)} unique 2023 buildings have a predicted score")
    print(f"  -> {JOINED_CSV}")
    return j


# ---------------------------------------------------------------------------
def write_db(joined: pd.DataFrame, model_version: str) -> None:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        sys.exit("[ERROR] psycopg2 not installed; pip install psycopg2-binary")

    # 与 Data wrangling/solar score.py 保持一致的连接信息
    DB_HOST = "3.26.146.10"
    DB_PORT = 5432
    DB_NAME = "melbourne_solar"
    DB_USER = "teamuser"
    DB_PASSWORD = "123456"

    print(f"[db] connecting to {DB_HOST}:{DB_PORT}/{DB_NAME} ...")
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS solar_score_v2 (
            structure_id_2023      INTEGER PRIMARY KEY,
            struct_id_2015         INTEGER,
            predicted_score_1_5    NUMERIC(4, 3),
            predicted_score_0_100  INTEGER CHECK (predicted_score_0_100 BETWEEN 0 AND 100),
            model_version          TEXT NOT NULL,
            computed_at            TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()

    rows = [
        (
            int(r.structure_id_2023),
            int(r.struct_id_2015),
            float(r.predicted_score_1_5),
            int(r.predicted_score_0_100),
            model_version,
        )
        for r in joined.itertuples(index=False)
    ]

    psycopg2.extras.execute_batch(
        cur,
        """
        INSERT INTO solar_score_v2
            (structure_id_2023, struct_id_2015,
             predicted_score_1_5, predicted_score_0_100, model_version)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (structure_id_2023) DO UPDATE SET
            struct_id_2015        = EXCLUDED.struct_id_2015,
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
    print(f"[db] wrote {len(rows)} rows to solar_score_v2")


# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-db", action="store_true",
        help="also write to PostgreSQL solar_score_v2 (default: only CSV)",
    )
    args = parser.parse_args()

    print(f"=== Step 5: infer (model={MODEL_NAME}) ===\n")
    preds = predict()
    cross = build_crosswalk(preds)
    joined = join_predictions_with_crosswalk(preds, cross)

    if args.write_db:
        write_db(joined, MODEL_NAME)
    else:
        print("\n[hint] DB write skipped; pass --write-db to upsert solar_score_v2")

    print("\ndone.")


if __name__ == "__main__":
    main()
