# Solar Score Model — 模型对比实验

测试多个候选模型 × 两种特征版本 × 两种样本权重方案，看能不能进一步降低 RMSE / 提高 Spearman。

**这个文件夹是实验性的，不进生产**。生产模型仍然是上层 `SolarScoreModel/` 里 `train.py` 训出来的那个。等实验结论确定，再决定要不要把生产模型切过去。

## 候选维度

| 维度 | 取值 |
|---|---|
| **模型** | `xgboost` / `lightgbm` / `catboost` / `random_forest` / `stacking` (xgb+lgb+cat → ridge meta) |
| **特征版本** | `v1` = 几何 + 辐照 + suburb（即生产用的那套）；`v2` = v1 + **Plan A：邻居遮挡代理**（每栋楼在 50m / 100m 半径内：邻居数、最高邻居高度、平均邻居高度、更高邻居数量、遮挡指数=Σ高差/距离） |
| **样本权重** | `none` = 等权；`patch` = `sample_weight = roof_patch_count`（**Plan B**：标签是 N 个 patch 评分的平均，N 越大方差越小） |

完整搜索空间 = 5 × 2 × 2 = **20 个组合**。

## 怎么跑

### 1. 装依赖
```bash
pip install lightgbm catboost
# (其他依赖在上层 SolarScoreModel/requirements.txt 已经装过)
```

### 2. 生成 v2 特征（一次性）
```bash
cd SolarScoreModel/experiments
python build_features_v2.py
```
输出：`../data/dataset_2015_v2.parquet`（在原 v1 基础上多 10 列邻居特征）

### 3. 跑实验

**全跑（20 个组合，CPU 估计 30~60 分钟）：**
```bash
python compare_models.py --all
```

**跑特定组合：**
```bash
python compare_models.py --features v2 --weights patch
python compare_models.py --features v2 --weights patch --models random_forest
```

**用 GPU：**
```bash
python compare_models.py --device gpu --features v2 --weights patch
python compare_models.py --device gpu --all
```

**控制 CPU 占用（避免闪退）：**
```bash
# 默认 n_jobs = CPU核数 / 2，留一半给系统
python compare_models.py --features v2 --weights patch

# 想再保守一点
python compare_models.py --n-jobs 4 --features v2 --weights patch

# 完全串行（最稳，最慢）
python compare_models.py --n-jobs 1 --features v2 --weights patch
```

外层（HalvingGridSearchCV / cross_val_score / Stacking）按 `--n-jobs` 并发，
**模型内部固定 n_jobs=1**，杜绝外层 × 内层嵌套爆出几十个线程的情况。

GPU 实际生效的模型：
- ✅ **xgboost** (`device="cuda"`)
- ✅ **catboost** (`task_type="GPU"`)
- ⚠️ **lightgbm** — pip wheel 是 CPU only，会自动落回 CPU 并打印提示。要 GPU 得自己用 `--gpu` 编译 LightGBM
- ⚠️ **random_forest** — sklearn 没 GPU 支持，自动落回 CPU
- ⚠️ **stacking** — xgb / cat 子模型走 GPU，lgb 子模型 + ridge meta 留在 CPU

**注意**：12k 行 × 30 多个特征是相对小的数据集，GPU 启动开销可能抵消加速。GPU 真正的优势在 >100k 行或者深度神经网。先跑一两个组合测一下你的卡有没有真的提速再决定要不要全跑 GPU。

每跑完一个组合，结果会**追加**到 `results/comparison.csv`（不会覆盖旧记录）。

### 4. 看结果
```bash
python -c "import pandas as pd; print(pd.read_csv('results/comparison.csv').sort_values('rmse').to_string())"
```

## 评判标准

- 主指标 **RMSE / Spearman**（同一 holdout，random_state=42 固定）
- **5-fold CV RMSE ± std** 验证是否过拟合
- 如果新特征 / 模型组合**同时**在 holdout 和 CV 上都比生产模型好 ≥3%，建议切换
- 提升 <2% 时考虑保留现状（边际收益 vs 复杂度）

## 设计原则

- 每个超参都由 `HalvingGridSearchCV` 5-fold CV 自动选，无主观干预
- 同一份 `train_test_split(random_state=42)` 横向比较，对所有候选公平
- 每行结果都附 `best_params`，便于复现
- `results/comparison.csv` 累积式追加，反复跑同一组合会留下多条记录（适合做随机性 sanity check）

## 文件清单

```
experiments/
├── README.md
├── build_features_v2.py    # Plan A：生成 v2 特征 parquet
├── compare_models.py       # 主入口：选模型 / 特征 / 权重 跑对比
└── results/
    └── comparison.csv      # 累积结果（首次跑时自动创建）
```
