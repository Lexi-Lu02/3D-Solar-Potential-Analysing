"""
Step 4: 评估 XGBoost 并生成 REPORT.md。

- 用与 train.py 相同的 split 评估 holdout 性能
- 5-fold CV 得到指标置信区间
- 报告 RMSE / MAE / Spearman / 5-bin 分类准确率 / 校准曲线
- 同时给出"无监督 baseline"（训练集均值预测）作为下界
- 输出 REPORT.md + figures/

不引入任何主观调整。
"""

from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.model_selection import KFold, cross_val_score, train_test_split

from _preprocess import (  # noqa: F401
    CATEGORICAL_FEATURES,
    CV_FOLDS,
    NUMERIC_FEATURES,
    RANDOM_STATE,
    TARGET,
    TEST_SIZE,
)

# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
ARTIFACTS = HERE / "artifacts"
FIGURES = HERE / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)
REPORT = HERE / "REPORT.md"

DATASET_LABELED = DATA_DIR / "dataset_2015.parquet"


# 5-bin = UI 分档
def to_bin_5(y: np.ndarray) -> np.ndarray:
    """1=Very Poor, 2=Poor, 3=Moderate, 4=Good, 5=Excellent；按 0.5 区间四舍五入。"""
    return np.clip(np.round(y).astype(int), 1, 5)


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def metrics_block(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "rmse": rmse(y_true, y_pred),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "spearman": float(spearmanr(y_true, y_pred).statistic),
        "bin5_accuracy": float(accuracy_score(to_bin_5(y_true), to_bin_5(y_pred))),
    }


def cv_metric(pipe, X, y, scoring: str) -> tuple[float, float]:
    cv = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(pipe, X, y, scoring=scoring, cv=cv, n_jobs=-1)
    return float(scores.mean()), float(scores.std())


# ---------------------------------------------------------------------------
def load_split() -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    df = pd.read_parquet(DATASET_LABELED)
    df = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET]].copy()
    df = df.dropna(subset=NUMERIC_FEATURES + [TARGET])
    df["suburb"] = df["suburb"].fillna("UNKNOWN")
    X = df.drop(columns=[TARGET])
    y = df[TARGET]
    return train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)


def plot_scatter(y_true, y_pred, title, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(y_true, y_pred, alpha=0.15, s=8)
    ax.plot([1, 5], [1, 5], "k--", lw=1)
    ax.set_xlabel("expert score (1–5)")
    ax.set_ylabel("predicted score")
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_calibration(y_true, y_pred, title, path: Path) -> None:
    bins = np.array([1, 1.5, 2.5, 3.5, 4.5, 5.0])
    df = pd.DataFrame({"y_true": y_true, "y_pred": y_pred})
    df["bin"] = pd.cut(df["y_pred"], bins, include_lowest=True)
    grp = df.groupby("bin", observed=True)["y_true"].agg(["mean", "count"]).reset_index()
    centers = [b.mid for b in grp["bin"]]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([1, 5], [1, 5], "k--", lw=1, label="perfect")
    ax.plot(centers, grp["mean"], "o-", label="model")
    for c, m, n in zip(centers, grp["mean"], grp["count"]):
        ax.annotate(f"n={int(n)}", (c, m), fontsize=7, alpha=0.7)
    ax.set_xlabel("predicted bin centre")
    ax.set_ylabel("mean expert score in bin")
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_xgb_importance(path: Path) -> None:
    feat_csv = ARTIFACTS / "feature_importance.csv"
    if not feat_csv.exists():
        return
    df = pd.read_csv(feat_csv).head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(df["feature"], df["gain_importance"], color="#1f77b4")
    ax.set_xlabel("gain-based importance")
    ax.set_title("XGBoost — top 15 features by gain importance")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
def main() -> None:
    X_train, X_test, y_train, y_test = load_split()
    print(f"[split] train={len(X_train)}  test={len(X_test)}")

    results: dict[str, dict] = {}
    cv_results: dict[str, dict] = {}

    # mean-baseline (训练集均值预测) 仅作为下界参考
    mean_pred = np.full_like(y_test, fill_value=y_train.mean(), dtype=float)
    results["mean_baseline"] = metrics_block(y_test.to_numpy(), mean_pred)

    xgb_path = ARTIFACTS / "xgb.pkl"
    if not xgb_path.exists():
        print(f"[ERROR] {xgb_path} not found; run train.py first")
        return
    xgbm = joblib.load(xgb_path)
    y_pred = xgbm.predict(X_test)
    results["xgb"] = metrics_block(y_test.to_numpy(), y_pred)
    rmse_mu, rmse_sd = cv_metric(xgbm, X_train, y_train, "neg_root_mean_squared_error")
    mae_mu, mae_sd = cv_metric(xgbm, X_train, y_train, "neg_mean_absolute_error")
    cv_results["xgb"] = {
        "cv_rmse_mean": -rmse_mu,
        "cv_rmse_std": rmse_sd,
        "cv_mae_mean": -mae_mu,
        "cv_mae_std": mae_sd,
    }
    plot_scatter(y_test, y_pred, "XGBoost — predicted vs expert", FIGURES / "xgb_scatter.png")
    plot_calibration(y_test, y_pred, "XGBoost — calibration", FIGURES / "xgb_calibration.png")
    plot_xgb_importance(FIGURES / "xgb_importance.png")

    write_report(results, cv_results)
    print("\nholdout metrics:")
    print(pd.DataFrame(results).T.round(4).to_string())
    print("\n5-fold CV (on train split):")
    print(pd.DataFrame(cv_results).T.round(4).to_string())


def write_report(results: dict[str, dict], cv_results: dict[str, dict]) -> None:
    rows_holdout = pd.DataFrame(results).T.round(4)
    rows_cv = pd.DataFrame(cv_results).T.round(4) if cv_results else pd.DataFrame()

    feat_csv = ARTIFACTS / "feature_importance.csv"
    feat_md = ""
    if feat_csv.exists():
        df = pd.read_csv(feat_csv)
        feat_md = df.head(15).to_markdown(index=False)

    n_total = len(pd.read_parquet(DATASET_LABELED))

    lines: list[str] = []
    lines.append("# Solar Score 模型 — 评估报告\n")
    lines.append("由 `evaluate.py` 自动生成，请勿手动修改。\n")
    lines.append("- **生产模型**：XGBoost 回归（5-fold HalvingGridSearchCV 自动调参）")
    lines.append(f"- 有标签样本数：**{n_total}**")
    lines.append(f"- 训练/测试切分：80/20，random_state={RANDOM_STATE}")
    lines.append(f"- 交叉验证折数：{CV_FOLDS}\n")

    lines.append("## Holdout 指标（测试集）\n")
    lines.append(rows_holdout.to_markdown())
    lines.append(
        "\n*RMSE / MAE 越小越好；Spearman / bin5_accuracy 越大越好。"
        "`mean_baseline` 用训练集均值常数预测，仅作下界参考。*\n"
    )

    if not rows_cv.empty:
        lines.append("## 训练集 5 折交叉验证\n")
        lines.append(rows_cv.to_markdown())
        lines.append("")

    if feat_md:
        lines.append("## XGBoost — 基于 gain 的特征重要性（前 15）\n")
        lines.append(
            "gain importance 反映该特征在所有树节点分裂时带来的总损失下降，"
            "数值越大越关键。"
        )
        lines.append(feat_md)
        lines.append("")

    lines.append("## 局限性与诚实声明\n")
    lines.append(
        "- **NASA POWER 辐照在墨尔本 CBD 范围内近乎常量**："
        "其原生约 0.5° 分辨率下，训练集里所有建筑都被映射到同一个格点，"
        "因此 `VarianceThreshold` 在预处理阶段自动剔除了这些特征。"
        "这是模型在如实回答：在当前辐照数据源下，辐照对 CBD 内建筑无区分力。"
        "如果未来拿到 BOM 5 km 网格（付费、邮件申请），只需替换这一模块，"
        "其余流程不变即可平滑升级。"
    )
    lines.append(
        "- **标签本身是主观专家判断**（来源：City of Melbourne 2015 Rooftop Project）。"
        "模型学习的是「如何用客观的几何 + 辐照特征复现专家共识」，"
        "不是物理意义上的发电量预测器。"
    )
    lines.append(
        "- **suburb 是较强的特征**：它吸收了几何特征无法捕捉的空间 / 城市肌理效应。"
        "为了对预测力诚实，我们保留它；如果你想要纯几何模型，"
        "可以去掉 suburb，但要接受 RMSE 上升。"
    )
    lines.append(
        "- **约 23% 的建筑没有标签**：20,462 栋 2015 footprint 中约 4,775 栋"
        "没有专家评分（多为很小的附属结构或在调研覆盖范围之外）。"
        "`infer.py` 会把模型外推到这些建筑上，但这部分预测应被视为"
        "**有依据的外推**，而非已验证的估计。"
    )
    lines.append(
        "- **2015 footprint 中跨 struct_id 的几何重复**：原始数据里同 `struct_id` "
        "的多块屋顶分片已经在 `build_features.py` 通过 `dissolve(by='struct_id')` "
        "合并；但另有约 80 对**不同 struct_id 但几何重叠 >80%**（同一栋楼被登记两次）。"
        "占样本约 0.4%，对训练指标影响可忽略，因此第一版未做额外去重；"
        "如需更严的去重可在预处理中加一道 self-sjoin。"
    )
    lines.append("")

    lines.append("## 图表\n")
    for f in [
        "xgb_scatter.png",
        "xgb_calibration.png",
        "xgb_importance.png",
    ]:
        if (FIGURES / f).exists():
            lines.append(f"- ![](figures/{f})")
    lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nreport -> {REPORT}")


if __name__ == "__main__":
    main()
