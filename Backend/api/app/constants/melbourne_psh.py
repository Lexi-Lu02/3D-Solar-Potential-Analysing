"""
Melbourne CBD solar yield constants.

单一数据来源。数据管线 (`Data wrangling/build_geojson.py`) 目前仍内嵌这些值;
Phase F 前端迁移完成后,那边应改为调用 API 而非读静态 GeoJSON。

─────────────────────────────────────────────────────────────────────────────
年度 kWh 公式（/buildings/{id}/yield 端点）

    kwh_monthly[i] = usable_roof_area
                     × PANEL_EFFICIENCY
                     × PERFORMANCE_RATIO
                     × MONTHLY_PSH[i]
                     × DAYS_IN_MONTH[i]

    kwh_annual = sum(kwh_monthly)   ← 保证月度加总与年度数字完全一致

─────────────────────────────────────────────────────────────────────────────
数据来源说明

MONTHLY_PSH 来自 NASA POWER 气候学 API（20 年均值 2001–2020），
坐标：lat=-37.818, lng=144.968，参数：ALLSKY_SFC_SW_DWN，单位 kWh/m²/day。

原始 NASA 年均为 4.51 PSH/day，比 BOM 站点 086338（墨尔本气象站）地面实测
值约高 10%。为消除卫星数据对阴天沿海城市的系统性偏高偏差，对 12 个月度值
等比例缩放（系数 = 4.1 / 4.51 = 0.9090…），使年均恰好等于 BOM 验证值 4.1：

    sum(MONTHLY_PSH[i] × DAYS_IN_MONTH[i]) / 365 ≈ 4.10 ✓

缩放后保留了 NASA POWER 的季节性形状（夏高冬低），同时锚定 BOM 的年均基准，
避免 /yield 的月度加总与 /buildings/{id} 的年度概要数字出现 10% 矛盾。

如需更新（例如 30 年气候基准周期约 2030 年更新时），重新 fetch：
    https://power.larc.nasa.gov/api/temporal/climatology/point
        ?parameters=ALLSKY_SFC_SW_DWN&community=RE
        &longitude=144.968&latitude=-37.818&format=JSON
然后用新年均值重新计算缩放系数。
"""

from __future__ import annotations

from typing import Final

# --- 年度常量 ---------------------------------------------------------------

PANEL_EFFICIENCY: Final[float] = 0.20
"""光伏板转换效率（20%），对应标准商业晶硅组件。"""

PERFORMANCE_RATIO: Final[float] = 0.75
"""系统性能比：逆变器损耗、灰尘、线缆、温度等综合折减。"""

PEAK_SUN_HOURS: Final[float] = 4.1
"""墨尔本 CBD 日均峰值日照时数（年均），BOM 站点 086338 实测基准值。"""

DAYS_PER_YEAR: Final[int] = 365

# --- 月度 PSH（NASA POWER × BOM 缩放，系数 0.9090） -------------------------
# 索引 0 = 1月（January），索引 11 = 12月（December）。

MONTHLY_PSH: Final[tuple[float, ...]] = (
    6.56,  # 1月  Jan  (原始 7.22 × 0.909)
    5.71,  # 2月  Feb  (原始 6.28 × 0.909)
    4.59,  # 3月  Mar  (原始 5.05 × 0.909)
    3.18,  # 4月  Apr  (原始 3.50 × 0.909)
    2.16,  # 5月  May  (原始 2.38 × 0.909)
    1.69,  # 6月  Jun  (原始 1.86 × 0.909)
    1.86,  # 7月  Jul  (原始 2.04 × 0.909)
    2.61,  # 8月  Aug  (原始 2.87 × 0.909)
    3.72,  # 9月  Sep  (原始 4.09 × 0.909)
    4.92,  # 10月 Oct  (原始 5.42 × 0.909)
    5.78,  # 11月 Nov  (原始 6.36 × 0.909)
    6.49,  # 12月 Dec  (原始 7.14 × 0.909)
)
# 验证：sum(psh[i] * days[i]) / 365 ≈ 4.10

DAYS_IN_MONTH: Final[tuple[int, ...]] = (
    31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
)

MONTH_NAMES: Final[tuple[str, ...]] = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)
