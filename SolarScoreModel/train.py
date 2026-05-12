"""Step 3: train LightGBM regressor.

Hyperparameters (n_estimators / num_leaves / learning_rate) tuned by 5-fold
HalvingGridSearchCV — no manual choices.

Choice of LightGBM justified by 5-models × 2-features × 2-weights benchmark
(see README "Why LightGBM").
"""

from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

# silence noisy "X does not have valid feature names" from LightGBM sklearn wrapper
# during CV (Pipeline → array → LGBMRegressor.predict). harmless.
warnings.filterwarnings(
    "ignore", message="X does not have valid feature names"
)

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.experimental import enable_halving_search_cv  # noqa: F401
from sklearn.model_selection import HalvingGridSearchCV, KFold, train_test_split
from sklearn.pipeline import Pipeline
import lightgbm as lgb

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

# default outer parallelism = half the cores; inner kept at 1 to avoid nesting
DEFAULT_N_JOBS = max(1, (os.cpu_count() or 4) // 2)


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
          f"suburbs: {df['suburb'].nunique()}, "
          f"features: {len(NUMERIC_FEATURES)} numeric + {len(CATEGORICAL_FEATURES)} categorical")
    return df.drop(columns=[TARGET]), df[TARGET]


def train_lgb(X_train, y_train, n_jobs: int = DEFAULT_N_JOBS) -> Pipeline:
    print("\n--- training LightGBM (HalvingGridSearchCV) ---")
    pre = make_preprocessor()
    base = lgb.LGBMRegressor(
        random_state=RANDOM_STATE, n_jobs=1, verbose=-1,
    )
    pipe = Pipeline(steps=[("pre", pre), ("model", base)])
    grid = {
        "model__n_estimators": [200, 400, 800],
        "model__num_leaves": [15, 31, 63],
        "model__learning_rate": [0.03, 0.1],
    }
    search = HalvingGridSearchCV(
        pipe,
        grid,
        cv=KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE),
        scoring="neg_root_mean_squared_error",
        random_state=RANDOM_STATE,
        n_jobs=n_jobs,
        factor=3,
        verbose=0,
    )
    search.fit(X_train, y_train)
    print(f"  best params: {search.best_params_}")
    return search.best_estimator_


def export_feature_importance(pipe: Pipeline, out_path: Path) -> None:
    pre: ColumnTransformer = pipe.named_steps["pre"]
    feature_names = pre.get_feature_names_out()
    booster = pipe.named_steps["model"]
    importances = booster.feature_importances_  # split count by default
    df = pd.DataFrame(
        {"feature": feature_names, "split_importance": importances}
    ).sort_values("split_importance", ascending=False)
    df.to_csv(out_path, index=False)
    print(f"  -> {out_path}")
    print("  top 8 LightGBM split-based importances:")
    print(df.head(8).to_string(index=False))


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--n-jobs", type=int, default=DEFAULT_N_JOBS,
        help=f"outer HGS / CV parallelism, default = cpu/2 = {DEFAULT_N_JOBS}",
    )
    args = parser.parse_args()
    n_jobs = max(1, args.n_jobs)
    print(f"[runtime] n_jobs={n_jobs}  cpu_count={os.cpu_count()}")

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

    model = train_lgb(X_train, y_train, n_jobs=n_jobs)
    joblib.dump(model, ARTIFACTS / "lgb.pkl")
    print(f"  saved -> {ARTIFACTS / 'lgb.pkl'}")
    export_feature_importance(model, ARTIFACTS / "feature_importance.csv")

    print("\ntraining done.")


if __name__ == "__main__":
    main()
