"""
kWh 光伏发电量计算服务。

公式（单月）：
    kwh_monthly[i] = usable_roof_area
                     × PANEL_EFFICIENCY
                     × PERFORMANCE_RATIO
                     × MONTHLY_PSH[i]
                     × DAYS_IN_MONTH[i]

年度值为 12 个月之和（不是用 PEAK_SUN_HOURS×365 重新算），保证
/yield 响应中 kwh_annual == sum(kwh_monthly) 精确成立。

月度 PSH 来自 NASA POWER 卫星气候学数据，经 BOM 站点 086338 年均校准，
见 constants/melbourne_psh.py 中的详细说明。
"""

from __future__ import annotations

import logging
import math
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from ..constants.melbourne_psh import (
    DAYS_IN_MONTH,
    MONTH_NAMES,
    MONTHLY_PSH,
    PANEL_EFFICIENCY,
    PEAK_SUN_HOURS,
    PERFORMANCE_RATIO,
)
from ..models.schemas import YieldAssumptions, YieldMonthlyItem, YieldResponse
from ..sql import load

logger = logging.getLogger(__name__)


class BuildingNotFoundForYield(Exception):
    """建筑主键不存在时抛出（yield 路由同样需要 404）。"""

    def __init__(self, id: int):
        super().__init__(f"building {id} not found")
        self.id = id


def fetch_yield(conn: Connection, id: int) -> YieldResponse:
    """
    查询 usable_roof_area，用公式计算月度和年度 kWh，返回 YieldResponse。

    - 建筑不存在 → BuildingNotFoundForYield（路由层转 404）
    - 建筑存在但无光伏数据 → has_data=False，kwh_annual=0，kwh_monthly=[]
    """
    sql = load("yield_by_id")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, {"id": id})
        row = cur.fetchone()

    if row is None:
        raise BuildingNotFoundForYield(id)

    usable_area = _safe_float(row.get("usable_roof_area"))
    has_data = row.get("usable_roof_area") is not None and usable_area > 0

    if not has_data:
        return YieldResponse(
            structure_id=int(row["structure_id"]),
            has_data=False,
            kwh_annual=0,
            kwh_monthly=[],
            assumptions=YieldAssumptions(
                panel_efficiency=PANEL_EFFICIENCY,
                performance_ratio=PERFORMANCE_RATIO,
                peak_sun_hours_annual=PEAK_SUN_HOURS,
                usable_roof_area_m2=0.0,
            ),
        )

    monthly = _compute_monthly(usable_area)
    kwh_annual = sum(item.kwh for item in monthly)

    return YieldResponse(
        structure_id=int(row["structure_id"]),
        has_data=True,
        kwh_annual=round(kwh_annual),
        kwh_monthly=monthly,
        assumptions=YieldAssumptions(
            panel_efficiency=PANEL_EFFICIENCY,
            performance_ratio=PERFORMANCE_RATIO,
            peak_sun_hours_annual=PEAK_SUN_HOURS,
            usable_roof_area_m2=round(usable_area, 1),
        ),
    )


# --- 内部函数 ----------------------------------------------------------------


def _compute_monthly(usable_area: float) -> list[YieldMonthlyItem]:
    """计算 12 个月的 kWh 列表。索引 0 = 1月。"""
    result: list[YieldMonthlyItem] = []
    for i in range(12):
        kwh = (
            usable_area
            * PANEL_EFFICIENCY
            * PERFORMANCE_RATIO
            * MONTHLY_PSH[i]
            * DAYS_IN_MONTH[i]
        )
        result.append(
            YieldMonthlyItem(
                month=MONTH_NAMES[i],
                days=DAYS_IN_MONTH[i],
                psh=MONTHLY_PSH[i],
                kwh=round(kwh),
            )
        )
    return result


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(f) or math.isinf(f):
        return 0.0
    return f
