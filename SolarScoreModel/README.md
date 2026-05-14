# SolarScoreModel — 数据驱动的 Solar Score

## 为什么有这个模块

原 `Data wrangling/solar score.py` 用 `ALPHA = 0.5` 把 quality 和 quantity 等权相加得到 0–100 的 solar score。这个 0.5 是拍脑袋定的，没有数据支撑——任何人问"为什么不是 0.4 或 0.7"都答不上来。

本模块用 **2015 同期数据**（City of Melbourne 2015 building outlines + 2015 Rooftop Project 专家评分 + 2015 NASA POWER 历史辐照）训练一个 **LightGBM 回归模型**（5-fold HalvingGridSearchCV 自动调参），学好之后**把权重套到生产数据库里 19,326 栋 2023 buildings 上**给出 0–100 的预测分。

**核心原则：所有处理步骤都来自客观数据源 + 标准统计变换，零主观权重 / 阈值。**

---

## 流程：训练 ↔ 推理 双线对称

```
┌────────────────── 训练（一次性，决定权重） ─────────────────┐
│ 2015 footprint CSV      ─┐                                  │
│ 2015 patch shapefile    ─┼─→ build_features.py             │
│ 2015 NASA POWER cache   ─┘   ↓ 同特征工程函数               │
│                              dataset_2015.parquet          │
│                              ↓ train.py                     │
│                              artifacts/lgb.pkl ← 学到权重   │
└──────────────────────────────────────────────────────────────┘
                                  │
                                  │ 套用同样的权重
                                  ↓
┌─────────────── 推理（每次重跑都更新生产分数） ────────────┐
│ PG buildings + precincts  ─→ build_features_2023.py        │
│                                ↓ 同特征工程函数             │
│                                dataset_2023.parquet         │
│                                ↓ infer.py                   │
│                                solar_score_v2 表            │
│                                ↓ Backend SQL 自动 join     │
│                                前端 0–100 分                │
└──────────────────────────────────────────────────────────────┘
```

**特征工程函数在 `_features.py`，训练和推理共用同一份代码**，确保两条线的特征定义零差异。

---

## 特征清单（共 21 数值 + 1 类别，全部物理可解释）

| 类 | 个数 | 字段 | 物理含义 |
|---|---|---|---|
| 几何 | 7 | `roof_area_m2`、`roof_perimeter_m`、`roof_compactness`、`building_height_m`、`roof_top_elevation_m`、`roof_aspect_deg`、`roof_elongation` | 屋顶尺寸、紧凑度、高度、长轴方向 |
| 辐照 | 4 | `annual_solar_kwh_m2`、`winter_solar_kwh_m2_day`、`summer_solar_kwh_m2_day`、`solar_seasonality` | NASA POWER 2015 历史日射；CBD 范围内常量，被 VarianceThreshold 自动剔 |
| 邻居遮挡 | 10 | `nbr_count_50m/100m`、`nbr_max_height_50m/100m`、`nbr_mean_height_50m/100m`、`nbr_taller_count_50m/100m`、`nbr_shading_index_50m/100m` | 50m / 100m 半径内的邻居数量 / 最高 / 平均高度 / 比自己高的数量 / 加权遮挡指数 |
| 类别 | 1 | `suburb`（训练时 = 2015 footprint 字段；推理时 = `precincts.name` 查表，**14 个字符串完全相同**） | 街区效应代理 |

**故意不用的特征**：

- ❌ `lat` / `lng`：CBD 几公里尺度上对 solar score 没有物理意义，仅作空间过拟合代理。早期实验表明 lng 会被模型刷成 #1 重要特征，方法论上无法辩护
- ❌ `roof_type`：2015 footprint 数据集没有这个字段；为保训练 / 推理对称放弃
- ❌ `usable_ratio` / `dominant_rating` / `excellent_area`：从 `solar_score_avg` 派生 → 数据泄漏
- ❌ Google Solar API 输出（`solar_api_cache`）：是当下数据，与 2015 标签时间不匹配，且内含其他模型的主观处理

---

## 为什么是 LightGBM

最初做了一轮 **5 模型 × 2 特征版本 × 2 样本权重方案 = 20 组合**的对比实验（CPU、固定 split、固定 5-fold CV）。完整数据：

| rank | features | weights | model | RMSE | MAE | Spearman | CV RMSE | 训练秒 |
|---:|:---|:---|:---|---:|---:|---:|---:|---:|
| 🥇 1 | v2 | none | **lightgbm** | **0.683** | **0.507** | **0.652** | 0.708 | 6.2 |
| 🥈 2 | v2 | none | stacking | 0.687 | 0.508 | 0.648 | — | 5.6 |
| 🥉 3 | v2 | none | random_forest | 0.693 | 0.516 | 0.643 | 0.717 | 74.7 |
| 4 | v2 | patch | random_forest | 0.693 | 0.520 | 0.643 | 0.714 | 161.6 |
| 5 | v2 | none | catboost | 0.701 | 0.526 | 0.634 | 0.722 | 56.9 |
| 6 | v2 | none | xgboost | 0.705 | 0.528 | 0.631 | 0.726 | 7.8 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 18 | v1 | none | xgboost | 0.748 | 0.560 | 0.591 | 0.767 | 6.0 |

`features`：v1 = 几何 + 辐照 + suburb；v2 = v1 + 邻居遮挡代理（10 个特征）
`weights`：none = 等权；patch = 训练时 sample_weight = roof_patch_count

**三个明确结论**：

1. **LightGBM + v2 特征 + 不加样本权重**胜出，RMSE 比 XGBoost(v1, none) 的 0.748 降 8.7%
2. **邻居遮挡特征（v2）全员有效**：5 个模型都改善，平均 -5~8% RMSE
3. **样本权重（patch）反而伤害精度**——5 个模型 4 个变差。"标签是 N 个 patch 平均，N 越大方差越小应该加权"这个**直觉被数据反驳**

后来又做了一轮**清理特征空间**（去掉 lat/lng + 删 log1p / StandardScaler，只留 VarianceThreshold + OneHotEncoder），代价 RMSE 0.683 → 0.701（+2.6%），换来纯物理可解释的特征列表，**论文里站得住脚**。

---

## 当前生产模型指标（2015 holdout）

| | RMSE | MAE | Spearman | bin5 准确率 |
|---|---|---|---|---|
| 训练集均值 baseline | 0.945 | 0.74 | — | 56.4% |
| **LightGBM（生产）** | **0.701** | **0.524** | **0.629** | **59.8%** |
| 5-fold CV（训练集） | 0.724 ± 0.019 | 0.541 ± 0.015 | — | — |

特征重要性 top 8（split-based）：

```
1. roof_area_m2          596   ← 屋顶面积
2. nbr_mean_height_100m  528   ← 邻居平均高度
3. roof_top_elevation_m  498   ← 屋顶绝对海拔
4. nbr_max_height_100m   447   ← 最高邻居
5. nbr_count_100m        446   ← 邻居密度
6. building_height_m     434
7. nbr_max_height_50m    380
8. roof_perimeter_m      303
```

全部物理可解释。

---

## 目录结构

```
SolarScoreModel/
├── README.md                     # 本文件
├── REPORT.md                     # 由 evaluate.py 自动生成
├── requirements.txt
│
├── _preprocess.py                # 共享：特征清单 + LightGBM-friendly 极简预处理
├── _features.py                  # 共享：几何 / 辐照 / 邻居 三个核心特征工程函数
├── _db.py                        # 共享：PostgreSQL 连接 helper（读 Backend/.env）
│
├── fetch_data.py                 # Step 1: 校验 2015 footprint CSV + 拉 NASA POWER 缓存
├── build_features.py             # Step 2-train: 生成 dataset_2015.parquet（训练用）
├── build_features_2023.py        # Step 2-infer: 从 PG 拉 → dataset_2023.parquet（推理用）
├── train.py                      # Step 3: 训练 LightGBM（HGS 自动调参）
├── evaluate.py                   # Step 4: 评估 + REPORT.md
├── infer.py                      # Step 5: 对 dataset_2023 跑预测 + 写 solar_score_v2
│
├── data/
│   ├── raw_2015/
│   │   ├── footprints/building-outlines-2015.csv     # 用户手动下载（CC BY）
│   │   └── nasa_power/                               # NASA POWER 缓存
│   ├── labels_2015.parquet
│   ├── dataset_2015.parquet                          # 训练（15,687 有标签）
│   ├── dataset_2015_full.parquet                     # 训练全集（20,462 含无标签）
│   └── dataset_2015.parquet 已删，由 build 重新生成
│   └── dataset_2023.parquet                          # 推理（19,326 栋 2023）
├── artifacts/
│   ├── lgb.pkl
│   ├── feature_importance.csv
│   ├── split.json
│   └── predictions_2023.csv                          # 推理输出
└── figures/
    ├── lgb_scatter.png
    ├── lgb_calibration.png
    └── lgb_importance.png
```

---

## 数据源

| 阶段 | 角色 | 来源 |
|---|---|---|
| 训练 | 几何 | `data/raw_2015/footprints/building-outlines-2015.csv` (City of Melbourne，CC BY，**用户手动下载**) |
| 训练 | 标签 | `Data wrangling/green roof solar data/mga55_gda95_green_roof_solar.shp` (仓库已含) |
| 训练 | 辐照 | NASA POWER `ALLSKY_SFC_SW_DWN` 2015 daily（fetch_data.py 自动拉） |
| **推理** | 几何 + 高度 + 区位 | **PostgreSQL `buildings` + `precincts` 表（直连 DB）** |
| 推理 | 辐照 | 复用训练时拉的 NASA POWER 缓存（CBD 内常量，年份不影响） |

DB 凭证从 `Backend/.env` 自动读取（`_db.py` 的轻量级解析），不写死。

---

## 怎么跑

```bash
cd SolarScoreModel
pip install -r requirements.txt

# === 训练阶段（只在调参 / 重训时需要） ===
python fetch_data.py              # 拉 NASA POWER（首次）
python build_features.py          # 2015 训练数据
python train.py                   # 训练 LightGBM
python evaluate.py                # 写 REPORT.md

# === 推理阶段（每次想刷新生产分数都跑这两条） ===
python build_features_2023.py     # 从 PG 拉 + 算 2023 特征
python infer.py --write-db        # 跑预测 + 写入 solar_score_v2
```

**控制 CPU 占用**：`train.py` / `evaluate.py` 默认外层并发度 = CPU 核数 / 2，避免占满系统闪退。要更保守传 `--n-jobs 4`，要完全串行传 `--n-jobs 1`。

---

## Backend 集成

- [Backend/app/sql/building_by_id.sql](../Backend/app/sql/building_by_id.sql) `LEFT JOIN solar_score_v2 ON v2.structure_id = b.structure_id`
- [Backend/app/services/building_query.py](../Backend/app/services/building_query.py) 优先级：`solar_score_v2` → `rooftop_solar.solar_score_avg` 线性映射 → NULL
- 前端契约 `solar_score: int 0–100 | null` 不变

---

## 局限性与诚实声明

- **NASA POWER 辐照在墨尔本 CBD 范围内近乎常量**：原生 ~0.5° 分辨率下所有建筑映射到同一格点，VarianceThreshold 自动剔除这些特征。这是模型如实表达"该数据源对 CBD 内建筑无区分力"。BOM 5 km 网格（付费、邮件申请）是后续升级路径，模块化设计便于替换。
- **标签是主观专家判断**（City of Melbourne 2015 Rooftop Project）。模型学习的是「如何用客观特征复现专家共识」，不是物理意义上的发电量预测器。
- **suburb 是较强特征**：吸收几何特征无法捕捉的街区效应。保留它是诚实表达——如果想要纯几何模型可去掉，但 RMSE 会再升一点。
- **roof_type 不在特征里**：2015 footprint 数据集没有这个字段；为保训练 / 推理对称放弃。如未来拿到 2015 同期 roof_type 标注（或用 LiDAR DSM 派生屋顶坡度方向），可显著降 RMSE。
- **跨 struct_id 几何重复**：约 80 对不同 ID 但几何重叠 >80% 的建筑（占 0.4%），本版未做额外去重。

---

## 设计准则（实施时严格遵守）

1. **零手工权重 / 阈值**：所有模型超参由 LightGBM HalvingGridSearchCV 学出
2. **零标签泄漏**：禁用 `usable_ratio` / `dominant_rating` / `excellent_area`
3. **纯物理特征**：不用 lat / lng 做空间过拟合代理
4. **训练 / 推理对称**：`_features.py` 共享同一份特征工程代码
5. **诚实评估**：5-fold CV + 校准曲线 + 全部对比实验诚实写进 README

---

## 还能怎么进一步降 RMSE

当前 RMSE 0.701 已经在标签噪声底（专家评分本身的 ±0.5~1 星不可约误差）附近。再降需要更好的特征：

- **2014–2018 LiDAR DSM 派生屋顶坡度方向**：能把"屋顶到底朝南还是朝北"这个最关键的物理量加进来；预期可降到 0.60 量级
- **BOM 5 km 历史日照网格**（付费、邮件申请 climatedata@bom.gov.au）：替换 NASA POWER，让"建筑级辐照差异"可分辨

这两条都是后续升级路径。模块流程已经做了模块化解耦，替换数据源只需改 `fetch_data.py` + `_features.py`，模型层完全不动。
