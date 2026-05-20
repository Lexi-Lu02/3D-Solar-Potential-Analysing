"""
Solar kWh yield calculation service.

Monthly formula:
    kwh_monthly[i] = usable_roof_area
                     × PANEL_EFFICIENCY
                     × PERFORMANCE_RATIO
                     × MONTHLY_PSH[i]
                     × DAYS_IN_MONTH[i]

The annual total is the sum of the 12 monthly values (not recalculated from
PEAK_SUN_HOURS × 365), ensuring kwh_annual == sum(kwh_monthly) exactly.

Monthly PSH values come from NASA POWER satellite climatology data, calibrated
to the BOM station 086338 annual mean. See constants/melbourne_psh.py for details.
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


def fetch_yield_by_structure_id(conn: Connection, structure_id: int) -> YieldResponse | None:
    """
    Query usable_roof_area by structure_id and calculate monthly and annual kWh.

    Returns None if structure_id does not exist (router converts this to 404).
    Returns has_data=False with zero kWh if the building has no solar survey data.
    """
    sql = load("yield_by_structure_id")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, {"structure_id": structure_id})
        row = cur.fetchone()

    if row is None:
        return None

    usable_area = _safe_float(row.get("usable_roof_area"))
    has_data = row.get("usable_roof_area") is not None and usable_area > 0
    solar_score_avg = row.get("solar_score_avg")

    if not has_data:
        return YieldResponse(
            structure_id=int(row["structure_id"]),
            has_data=False,
            kwh_annual=0,
            kwh_monthly=[],
            solar_score_avg=float(solar_score_avg) if solar_score_avg is not None else None,
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
        solar_score_avg=float(solar_score_avg) if solar_score_avg is not None else None,
        assumptions=YieldAssumptions(
            panel_efficiency=PANEL_EFFICIENCY,
            performance_ratio=PERFORMANCE_RATIO,
            peak_sun_hours_annual=PEAK_SUN_HOURS,
            usable_roof_area_m2=round(usable_area, 1),
        ),
    )


# --- Internal helpers --------------------------------------------------------


def _compute_monthly(usable_area: float) -> list[YieldMonthlyItem]:
    """Compute kWh output for each of the 12 months. Index 0 = January."""
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
