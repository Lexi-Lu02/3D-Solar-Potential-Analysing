"""
在同一 holdout 上比较 5 个候选模型 × 2 种特征版本 × 2 种样本权重方案。

用法：
    python compare_models.py --features v1 --weights none
    python compare_models.py --features v2 --weights patch
    python compare_models.py --all                  # 跑全部 4 个组合
    python compare_models.py --models rf --features v2 --weights patch  # 只跑 RF
    python compare_models.py --device gpu --features v2 --weights patch # 用 GPU

GPU 支持：xgboost (device=cuda)、catboost (task_type=GPU)。
        lightgbm 默认 pip wheel 只有 CPU；random_forest / stacking-meta 没有 GPU
        路径——这些会自动 fallback 到 CPU 并打印一条提示。

候选模型：xgboost / lightgbm / catboost / random_forest / stacking
特征：
    v1   = 原 dataset_2015.parquet（几何 + 辐照 + suburb）
    v2   = v1 + 邻居遮挡代理（5 个特征 × 2 个半径，由 build_features_v2.py 产出）
样本权重：
    none  = 等权
    patch = sample_weight = roof_patch_count（标签可靠性的代理：N 越大方差越小）

输出：
    results/comparison.csv 每跑一组就追加一行（features, weights, model, rmse, mae, spearman, ...）

可重复：固定 random_state=42 + 同一 split + 同一 5-fold CV。
所有超参由 HalvingGridSearchCV 自动选，零主观干预。
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# 默认外层并发度 = CPU 核数的一半。避免占满 100% 让系统卡住/闪退。
DEFAULT_N_JOBS = max(1, (os.cpu_count() or 4) // 2)

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.experimental import enable_halving_search_cv  # noqa: F401
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import (
    HalvingGridSearchCV, KFold, cross_val_score, train_test_split,
)
from sklearn.pipeline import Pipeline

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from _preprocess import (  # type: ignore
    CATEGORICAL_FEATURES, CV_FOLDS, NUMERIC_FEATURES, RANDOM_STATE,
    TARGET, TEST_SIZE, make_preprocessor,
)

DATASET_V1 = ROOT / "data" / "dataset_2015.parquet"
DATASET_V2 = ROOT / "data" / "dataset_2015_v2.parquet"
RESULTS_CSV = HERE / "results" / "comparison.csv"
RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)

V2_EXTRA_COLS = [
    "nbr_count_50m", "nbr_max_height_50m", "nbr_mean_height_50m",
    "nbr_taller_count_50m", "nbr_shading_index_50m",
    "nbr_count_100m", "nbr_max_height_100m", "nbr_mean_height_100m",
    "nbr_taller_count_100m", "nbr_shading_index_100m",
]


# ---------------------------------------------------------------------------
def rmse(y, yhat):
    y = np.asarray(y); yhat = np.asarray(yhat)
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def metrics(y, yhat) -> dict:
    return {
        "rmse": rmse(y, yhat),
        "mae": float(mean_absolute_error(y, yhat)),
        "spearman": float(spearmanr(y, yhat).statistic),
    }


def cv_rmse(pipe, X, y, sw=None, n_jobs: int = DEFAULT_N_JOBS):
    cv = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    fit_params = {"model__sample_weight": sw} if sw is not None else None
    s = cross_val_score(
        pipe, X, y,
        scoring="neg_root_mean_squared_error", cv=cv, n_jobs=n_jobs,
        params=fit_params,
    )
    return float(-s.mean()), float(s.std())


# ---------------------------------------------------------------------------
def load_split(features_version: str):
    if features_version == "v1":
        path = DATASET_V1
        numeric = list(NUMERIC_FEATURES)
    elif features_version == "v2":
        path = DATASET_V2
        numeric = list(NUMERIC_FEATURES) + V2_EXTRA_COLS
    else:
        sys.exit(f"unknown features version: {features_version}")
    if not path.exists():
        sys.exit(f"[ERROR] {path} not found; for v2 run build_features_v2.py first")

    df = pd.read_parquet(path)
    keep_cols = numeric + CATEGORICAL_FEATURES + [TARGET, "roof_patch_count"]
    df = df[keep_cols].copy()
    df = df.dropna(subset=numeric + [TARGET])
    df["suburb"] = df["suburb"].fillna("UNKNOWN")
    weights_full = df["roof_patch_count"].fillna(1).clip(lower=1).to_numpy()

    X = df.drop(columns=[TARGET, "roof_patch_count"])
    y = df[TARGET]
    Xtr, Xte, ytr, yte, wtr, wte = train_test_split(
        X, y, weights_full, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    return Xtr, Xte, ytr, yte, wtr, wte, numeric


def make_preprocessor_for(numeric):
    """副本：用动态 numeric 列表替换 _preprocess 默认的 NUMERIC_FEATURES。"""
    from sklearn.compose import ColumnTransformer
    from sklearn.feature_selection import VarianceThreshold
    from sklearn.preprocessing import (
        FunctionTransformer, OneHotEncoder, StandardScaler,
    )
    from _preprocess import safe_log1p  # type: ignore

    numeric_pipe = Pipeline([
        ("log1p", FunctionTransformer(
            safe_log1p, validate=False, feature_names_out="one-to-one"
        )),
        ("var", VarianceThreshold(threshold=0.0)),
        ("scale", StandardScaler()),
    ])
    cat_pipe = Pipeline([
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer(
        [("num", numeric_pipe, numeric),
         ("cat", cat_pipe, CATEGORICAL_FEATURES)],
        remainder="drop", verbose_feature_names_out=False,
    )


# ---------------------------------------------------------------------------
def make_model(name: str, device: str = "cpu", n_jobs: int = DEFAULT_N_JOBS):
    """返回 (estimator, halving_grid 或 None)。grid=None 表示不做 HGS。

    device:
        cpu  — 全部用 CPU
        gpu  — XGBoost / CatBoost 用 GPU；LightGBM / RF / Stacking-meta 自动落回 CPU
    n_jobs:
        外层（HGS / cross_val_score / Stacking）的并发度。
        每个模型内部固定 n_jobs=1，避免外层 × 内层嵌套爆出几十个线程。
    """
    import xgboost as xgb
    import lightgbm as lgb
    from catboost import CatBoostRegressor

    use_gpu = device == "gpu"

    if name == "xgboost":
        kwargs = dict(
            objective="reg:squarederror", random_state=RANDOM_STATE,
            tree_method="hist", n_jobs=1,
        )
        if use_gpu:
            kwargs["device"] = "cuda"
        pipe_model = xgb.XGBRegressor(**kwargs)
        grid = {
            "model__n_estimators": [200, 400, 800],
            "model__max_depth": [3, 5, 7],
            "model__learning_rate": [0.03, 0.1],
        }
    elif name == "lightgbm":
        if use_gpu:
            print("  [info] LightGBM pip wheel is CPU-only; staying on CPU. "
                  "To use GPU, build LightGBM with --gpu and reinstall.")
        pipe_model = lgb.LGBMRegressor(
            random_state=RANDOM_STATE, n_jobs=1, verbose=-1,
        )
        grid = {
            "model__n_estimators": [200, 400, 800],
            "model__num_leaves": [15, 31, 63],
            "model__learning_rate": [0.03, 0.1],
        }
    elif name == "catboost":
        kwargs = dict(
            random_seed=RANDOM_STATE, verbose=False, thread_count=1,
        )
        if use_gpu:
            kwargs["task_type"] = "GPU"
            kwargs["devices"] = "0"
        pipe_model = CatBoostRegressor(**kwargs)
        grid = {
            "model__iterations": [200, 400, 800],
            "model__depth": [4, 6, 8],
            "model__learning_rate": [0.03, 0.1],
        }
    elif name == "random_forest":
        if use_gpu:
            print("  [info] sklearn RandomForest has no GPU support; staying on CPU. "
                  "(For GPU RF, install RAPIDS cuML — heavy dep, not auto-installed.)")
        # RF 自身可以并行树训练；HGS 外层用 n_jobs，RF 内层不再并行避免爆炸
        pipe_model = RandomForestRegressor(
            random_state=RANDOM_STATE, n_jobs=1,
        )
        grid = {
            "model__n_estimators": [300, 500, 800],
            "model__max_depth": [None, 12, 20],
            "model__min_samples_leaf": [1, 2, 4],
        }
    elif name == "stacking":
        xgb_kwargs = dict(
            n_estimators=400, max_depth=5, learning_rate=0.03,
            random_state=RANDOM_STATE, tree_method="hist", n_jobs=1,
        )
        cat_kwargs = dict(
            iterations=400, depth=6, learning_rate=0.03,
            random_seed=RANDOM_STATE, verbose=False, thread_count=1,
        )
        if use_gpu:
            xgb_kwargs["device"] = "cuda"
            cat_kwargs["task_type"] = "GPU"
            cat_kwargs["devices"] = "0"
            print("  [info] stacking: xgb+cat on GPU; lgb + ridge meta stay on CPU.")
        # GPU 模式下 stacking 内部 3 个基模型不能并行（会抢同一张卡）
        stacking_n_jobs = 1 if use_gpu else n_jobs
        pipe_model = StackingRegressor(
            estimators=[
                ("xgb", xgb.XGBRegressor(**xgb_kwargs)),
                ("lgb", lgb.LGBMRegressor(
                    n_estimators=400, num_leaves=31, learning_rate=0.03,
                    random_state=RANDOM_STATE, n_jobs=1, verbose=-1,
                )),
                ("cat", CatBoostRegressor(**cat_kwargs)),
            ],
            final_estimator=RidgeCV(),
            cv=KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE),
            n_jobs=stacking_n_jobs,
        )
        grid = None
    else:
        sys.exit(f"unknown model: {name}")
    return pipe_model, grid


# ---------------------------------------------------------------------------
def run_one(model_name: str, features_version: str, weights_mode: str,
            device: str = "cpu", n_jobs: int = DEFAULT_N_JOBS):
    Xtr, Xte, ytr, yte, wtr, _, numeric = load_split(features_version)
    sw = wtr if weights_mode == "patch" else None

    pre = make_preprocessor_for(numeric)
    base, grid = make_model(model_name, device=device, n_jobs=n_jobs)
    pipe = Pipeline([("pre", pre), ("model", base)])

    # GPU 上 xgb/cat 内层已经在 GPU 跑，HGS 外层并发会抢卡，强制串行
    if device == "gpu" and model_name in ("xgboost", "catboost"):
        hgs_n_jobs = 1
    else:
        hgs_n_jobs = n_jobs

    t0 = time.time()
    if grid is not None:
        search = HalvingGridSearchCV(
            pipe, grid,
            cv=KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE),
            scoring="neg_root_mean_squared_error",
            random_state=RANDOM_STATE, n_jobs=hgs_n_jobs, factor=3, verbose=0,
        )
        if sw is not None:
            search.fit(Xtr, ytr, model__sample_weight=sw)
        else:
            search.fit(Xtr, ytr)
        best = search.best_estimator_
        best_params = search.best_params_
    else:
        if sw is not None:
            pipe.fit(Xtr, ytr, model__sample_weight=sw)
        else:
            pipe.fit(Xtr, ytr)
        best = pipe
        best_params = {}
    train_secs = time.time() - t0

    holdout = metrics(yte, best.predict(Xte))
    cv_mu, cv_sd = (np.nan, np.nan)
    if grid is not None:  # CV 仅对参数化模型有意义；stacking 跳过省时间
        try:
            cv_mu, cv_sd = cv_rmse(best, Xtr, ytr, sw=sw, n_jobs=hgs_n_jobs)
        except Exception as e:
            print(f"  [warn] CV failed: {e}")

    row = {
        "features": features_version,
        "weights": weights_mode,
        "device": device,
        "model": model_name,
        "rmse": round(holdout["rmse"], 4),
        "mae": round(holdout["mae"], 4),
        "spearman": round(holdout["spearman"], 4),
        "cv_rmse_mean": round(cv_mu, 4) if not np.isnan(cv_mu) else None,
        "cv_rmse_std": round(cv_sd, 4) if not np.isnan(cv_sd) else None,
        "train_secs": round(train_secs, 1),
        "best_params": str(best_params),
    }
    return row


# ---------------------------------------------------------------------------
# 写 CSV 时的规范列序；新加列只往末尾或合理位置追加。
RESULT_COLS = [
    "features", "weights", "device", "model",
    "rmse", "mae", "spearman",
    "cv_rmse_mean", "cv_rmse_std",
    "train_secs", "best_params",
]


def append_result(row: dict) -> None:
    """追加一行；如果旧 CSV 缺列，自动按 RESULT_COLS 迁移整张表后再写。"""
    new_df = pd.DataFrame([row]).reindex(columns=RESULT_COLS)
    if not RESULTS_CSV.exists():
        new_df.to_csv(RESULTS_CSV, index=False)
        return

    old = pd.read_csv(RESULTS_CSV)
    if list(old.columns) == RESULT_COLS:
        # schema 一致，直接 append
        new_df.to_csv(RESULTS_CSV, mode="a", header=False, index=False)
        return

    # schema 不一致：把旧表 reindex 到新 schema，缺的列填默认值
    print(f"[migrate] CSV schema changed; rewriting with full schema")
    old_aligned = old.reindex(columns=RESULT_COLS)
    if "device" in (set(RESULT_COLS) - set(old.columns)):
        # 历史记录都是在加 --device 之前跑的 → 都是 CPU
        old_aligned["device"] = old_aligned["device"].fillna("cpu")
    merged = pd.concat([old_aligned, new_df], ignore_index=True)
    merged.to_csv(RESULTS_CSV, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--features", choices=["v1", "v2"], default="v1",
        help="特征版本：v1 (基础) 或 v2 (含邻居遮挡)",
    )
    parser.add_argument(
        "--weights", choices=["none", "patch"], default="none",
        help="样本权重：none 等权，patch 用 roof_patch_count",
    )
    parser.add_argument(
        "--models", nargs="+",
        default=["xgboost", "lightgbm", "catboost", "random_forest", "stacking"],
        help="要跑哪些模型（默认全跑）",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="跑全部 4 个 features×weights 组合（其它两个 flag 被忽略）",
    )
    parser.add_argument(
        "--device", choices=["cpu", "gpu"], default="cpu",
        help="计算设备：cpu (默认) 或 gpu。"
             "GPU 仅 xgboost / catboost 实际使用；其它模型自动落回 CPU。",
    )
    parser.add_argument(
        "--n-jobs", type=int, default=DEFAULT_N_JOBS,
        help=f"外层并发度（HGS / cross_val_score / Stacking）。"
             f"默认 = CPU 核数的一半 = {DEFAULT_N_JOBS}，避免占满系统导致闪退。"
             f" 传 1 完全串行；传更大数值更激进（注意稳定性）。"
             f" 模型内部固定 n_jobs=1 不参与嵌套。",
    )
    args = parser.parse_args()
    n_jobs = max(1, args.n_jobs)

    combos = (
        [(f, w) for f in ("v1", "v2") for w in ("none", "patch")]
        if args.all
        else [(args.features, args.weights)]
    )

    print(f"=== will run: combos={combos} models={args.models} "
          f"device={args.device} n_jobs={n_jobs} (cpu_count={os.cpu_count()}) ===\n")

    rows: list[dict] = []
    for f_ver, w_mode in combos:
        for m in args.models:
            print(f"\n--- features={f_ver}  weights={w_mode}  "
                  f"model={m}  device={args.device}  n_jobs={n_jobs} ---")
            try:
                row = run_one(m, f_ver, w_mode, device=args.device,
                              n_jobs=n_jobs)
            except Exception as e:
                print(f"  [error] {e}")
                continue
            rows.append(row)
            append_result(row)
            print(f"  rmse={row['rmse']}  mae={row['mae']}  "
                  f"spearman={row['spearman']}  "
                  f"cv_rmse={row['cv_rmse_mean']}±{row['cv_rmse_std']}  "
                  f"({row['train_secs']}s)")

    if rows:
        out = pd.DataFrame(rows)
        print(f"\n=== this run summary ===")
        print(out[["features", "weights", "device", "model", "rmse", "mae",
                   "spearman", "cv_rmse_mean", "train_secs"]].to_string(index=False))
        print(f"\nappended to {RESULTS_CSV}")


if __name__ == "__main__":
    main()
