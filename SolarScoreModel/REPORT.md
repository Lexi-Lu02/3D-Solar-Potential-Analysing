# Solar Score 模型 — 评估报告

由 `evaluate.py` 自动生成，请勿手动修改。

- **生产模型**：LightGBM 回归（5-fold HalvingGridSearchCV 自动调参）
- 有标签样本数：**15687**
- 训练/测试切分：80/20，random_state=42
- 交叉验证折数：5

## Holdout 指标（测试集）

|               |   rmse |    mae |   spearman |   bin5_accuracy |
|:--------------|-------:|-------:|-----------:|----------------:|
| mean_baseline | 0.9447 | 0.7414 |   nan      |          0.5637 |
| lgb           | 0.7009 | 0.5236 |     0.6289 |          0.5975 |

*RMSE / MAE 越小越好；Spearman / bin5_accuracy 越大越好。`mean_baseline` 用训练集均值常数预测，仅作下界参考。*

## 训练集 5 折交叉验证

|     |   cv_rmse_mean |   cv_rmse_std |   cv_mae_mean |   cv_mae_std |
|:----|---------------:|--------------:|--------------:|-------------:|
| lgb |         0.7238 |        0.0187 |         0.541 |       0.0149 |

## LightGBM — 基于 split 的特征重要性（前 15）

split importance 反映该特征在所有树节点上被选作分裂条件的次数，数值越大越关键。
| feature               |   split_importance |
|:----------------------|-------------------:|
| roof_area_m2          |                596 |
| nbr_mean_height_100m  |                528 |
| roof_top_elevation_m  |                498 |
| nbr_max_height_100m   |                447 |
| nbr_count_100m        |                446 |
| building_height_m     |                434 |
| nbr_max_height_50m    |                380 |
| roof_perimeter_m      |                303 |
| roof_elongation       |                252 |
| roof_aspect_deg       |                249 |
| nbr_mean_height_50m   |                248 |
| nbr_count_50m         |                228 |
| roof_compactness      |                207 |
| nbr_shading_index_50m |                178 |
| nbr_taller_count_100m |                168 |

## 局限性与诚实声明

- **NASA POWER 辐照在墨尔本 CBD 范围内近乎常量**：其原生约 0.5° 分辨率下，训练集里所有建筑都被映射到同一个格点，因此 `VarianceThreshold` 在预处理阶段自动剔除了这些特征。这是模型在如实回答：在当前辐照数据源下，辐照对 CBD 内建筑无区分力。如果未来拿到 BOM 5 km 网格（付费、邮件申请），只需替换这一模块，其余流程不变即可平滑升级。
- **标签本身是主观专家判断**（来源：City of Melbourne 2015 Rooftop Project）。模型学习的是「如何用客观的几何 + 邻居遮挡 + 辐照特征复现专家共识」，不是物理意义上的发电量预测器。
- **suburb 是较强的特征**：它吸收了几何特征无法捕捉的空间 / 城市肌理效应。为了对预测力诚实，我们保留它；如果你想要纯几何模型，可以去掉 suburb，但要接受 RMSE 上升。
- **约 23% 的建筑没有标签**（20,462 栋 2015 footprint 中约 4,775 栋没有专家评分，多为很小的附属结构或在调研覆盖范围之外）。**这些建筑不参与训练**——`infer.py` 的输出只覆盖训练时见过的建筑空间。
- **2015 footprint 中跨 struct_id 的几何重复**：原始数据里同 `struct_id` 的多块屋顶分片已经在 `build_features.py` 通过 `dissolve(by='struct_id')` 合并；但另有约 80 对**不同 struct_id 但几何重叠 >80%**（同一栋楼被登记两次）。占样本约 0.4%，对训练指标影响可忽略，因此第一版未做额外去重。

## 图表

- ![](figures/lgb_scatter.png)
- ![](figures/lgb_calibration.png)
- ![](figures/lgb_importance.png)
