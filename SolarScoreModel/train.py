"""
Step 3: 训练 XGBoost 回归模型。

预处理（见 _preprocess.py）：
- log1p（对正偏的面积/周长/高度类）
- VarianceThreshold(0) 自动剔除零方差特征（如 CBD 范围内常数化的 NASA POWER 列）
- StandardScaler 标准化
- suburb 做 one-hot

XGBoost 超参（n_estimators / max_depth / learning_rate）由 5-fold
HalvingGridSearchCV 在固定 grid 中自动选择，无任何主观干预。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.experimental import enable_halving_search_cv  # noqa: F401
from sklearn.model_selection import HalvingGridSearchCV, KFold, train_test_split
from sklearn.pipeline import Pipeline
import xgboost as xgb

from _preprocess import (
    CATEGORICAL_FEATURES,
    CV_FOLDS,
    NUMERIC_FEATURES,
    RANDOM_STATE,
    TARGET,
    TEST_SIZE,
    make_preprocessor,
)

# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
ARTIFACTS = HERE / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
DATASET_LABELED = DATA_DIR / "dataset_2015.parquet"


def load_dataset() -> tuple[pd.DataFrame, pd.Series]:
    if not DATASET_LABELED.exists():
        sys.exit(f"[ERROR] {DATASET_LABELED} missing; run build_features.py first")
    df = pd.read_parquet(DATASET_LABELED)
    cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET]
    df = df[cols].copy()
    n_before = len(df)
    df = df.dropna(subset=NUMERIC_FEATURES + [TARGET])
    df["suburb"] = df["suburb"].fillna("UNKNOWN")
    print(f"[data] {n_before} -> {len(df)} after dropna; "
          f"suburbs: {df['suburb'].nunique()}")
    return df.drop(columns=[TARGET]), df[TARGET]


def train_xgb(X_train, y_train) -> Pipeline:
    print("\n--- training XGBoost (HalvingGridSearchCV) ---")
    pre = make_preprocessor()
    base = xgb.XGBRegressor(
        objective="reg:squarederror",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        tree_method="hist",
    )
    pipe = Pipeline(steps=[("pre", pre), ("model", base)])
    grid = {
        "model__n_estimators": [200, 400, 800],
        "model__max_depth": [3, 5, 7],
        "model__learning_rate": [0.03, 0.1],
    }
    search = HalvingGridSearchCV(
        pipe,
        grid,
        cv=KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE),
        scoring="neg_root_mean_squared_error",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        factor=3,
        verbose=0,
    )
    search.fit(X_train, y_train)
    print(f"  best params: {search.best_params_}")
    return search.best_estimator_


def export_xgb_importance(pipe: Pipeline, out_path: Path) -> None:
    pre: ColumnTransformer = pipe.named_steps["pre"]
    feature_names = pre.get_feature_names_out()
    booster = pipe.named_steps["model"]
    importances = booster.feature_importances_  # gain-based
    df = pd.DataFrame(
        {"feature": feature_names, "gain_importance": importances}
    ).sort_values("gain_importance", ascending=False)
    df.to_csv(out_path, index=False)
    print(f"  -> {out_path}")
    print("  top 8 XGB gain-based importances:")
    print(df.head(8).to_string(index=False))


def main() -> None:
    X, y = load_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    print(f"[split] train={len(X_train)}  test={len(X_test)}")

    split_meta = {
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "test_index": [int(i) for i in X_test.index.tolist()],
    }
    (ARTIFACTS / "split.json").write_text(json.dumps(split_meta), encoding="utf-8")

    xgbm = train_xgb(X_train, y_train)
    joblib.dump(xgbm, ARTIFACTS / "xgb.pkl")
    print(f"  saved -> {ARTIFACTS / 'xgb.pkl'}")
    export_xgb_importance(xgbm, ARTIFACTS / "feature_importance.csv")

    print("\ntraining done.")


if __name__ == "__main__":
    main()
