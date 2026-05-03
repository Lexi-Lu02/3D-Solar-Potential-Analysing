# SolarScoreModel — 数据驱动的 Solar Score 重构

## 为什么有这个模块

原 `Data wrangling/solar score.py` 用 `ALPHA = 0.5` 把 quality 和 quantity 等权相加得到 0–100 的 solar score。这个 0.5 是拍脑袋定的，没有数据支撑。

本模块用 **2015 同期数据**（City of Melbourne 2015 building outlines + 2015 Rooftop Project 专家评分 + 2015 NASA POWER 历史辐照）训练一个 **XGBoost 回归模型**（5-fold HalvingGridSearchCV 自动调参），每个特征的贡献都由数据学出来，而不是猜的。

**核心原则：所有处理步骤都来自客观数据源 + 标准统计变换，零主观权重/阈值。**

## 目录结构

```
SolarScoreModel/
├── fetch_data.py          # Step 1: 校验 footprint CSV + 拉 NASA POWER 2015 辐照
├── build_features.py      # Step 2: 几何特征 + 2015 标签生成 + 辐照采样
├── train.py               # Step 3: XGBoost 训练（5-fold CV 自动调参）
├── evaluate.py            # Step 4: 评估 + REPORT.md
├── infer.py               # Step 5: 全量预测 + 写库
├── requirements.txt
├── data/
│   ├── raw_2015/
│   │   ├── footprints/                    # 用户放 building-outlines-2015.csv 在这里
│   │   └── nasa_power/                    # NASA POWER 缓存
│   ├── labels_2015.parquet                # 重新生成的 2015 标签
│   ├── dataset_2015.parquet               # 训练集（有标签）
│   └── dataset_2015_full.parquet          # 全集（含无标签建筑，供推理）
├── artifacts/
│   ├── xgb.pkl                            # 训练好的 XGBoost 模型
│   ├── feature_importance.csv             # XGB gain-based 特征重要性
│   ├── predictions_2015.csv               # 全量预测（按 2015 struct_id）
│   ├── predictions_with_2023_id.csv       # 已 join 到 2023 ID 的最终结果
│   └── id_crosswalk_2015_to_2023.csv      # 2015 struct_id → 2023 structure_id
├── figures/                               # 散点图 / 校准曲线 / 特征重要性条形图
└── REPORT.md                              # 评估报告（auto-generated）
```

## 数据源

| 角色 | 数据 | 时期 | 状态 |
|---|---|---|---|
| 标签 (y) | `Data wrangling/green roof solar data/mga55_gda95_green_roof_solar.shp` 评分 patch (1–5) | 2015 | 仓库已含 |
| 几何特征 | `data/raw_2015/footprints/building-outlines-2015.csv` | 2015 | **用户手动下载（CC BY，City of Melbourne）** |
| 辐照特征 | NASA POWER `ALLSKY_SFC_SW_DWN` 2015 daily | 2015 | 自动拉取 |

## 怎么跑

```bash
cd SolarScoreModel
pip install -r requirements.txt

python fetch_data.py            # 校验 + 拉 NASA POWER
python build_features.py        # 生成 dataset_2015.parquet
python train.py                 # 训练 XGBoost
python evaluate.py              # 写 REPORT.md
python infer.py --write-db      # 推理并写入 solar_score_v2（去掉 --write-db 只落盘 CSV）
```

## 与 `Data wrangling/` 的关系

- `Data wrangling/` 仍然负责 **2023 footprint** 的清洗 + 当前 DB 的 buildings/rooftop_solar 表
- `SolarScoreModel/` 完全在 **2015 ID 空间**内闭环训练
- 仅在最后 `infer.py` 写库时通过空间最近邻把 2015 `struct_id` 映射到 2023 `structure_id`，结果写入新表 `solar_score_v2`，**不修改现有 buildings/rooftop_solar 表**

## 设计准则（请实施时遵守）

1. **零手工权重**：所有模型系数由 RidgeCV / XGBoost CV 学出
2. **零手工阈值**：日照分箱、特征筛选都用统计量驱动（log1p / StandardScaler / 百分位）
3. **零标签泄漏**：不引入 `usable_ratio`、`dominant_rating`、`excellent_area` 等从标签派生的字段
4. **诚实评估**：5-fold CV + 校准曲线，不刻意优化"打败 0.5 baseline"
