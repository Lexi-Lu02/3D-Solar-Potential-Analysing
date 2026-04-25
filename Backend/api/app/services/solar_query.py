"""
Solar API cache lookup service.

Returns the raw solar_api_cache record for a single building, identified by
buildings.id (the surrogate PK). Used by GET /api/v1/buildings/{id}/solar.
"""

from __future__ import annotations

import logging
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from ..models.schemas import SolarCacheResponse
from ..sql import load

logger = logging.getLogger(__name__)


def fetch_solar_by_structure_id(conn: Connection, structure_id: int) -> SolarCacheResponse | None:
    """
    Return the solar_api_cache row for the given City of Melbourne structure_id.
    Returns None if no matching record exists (router converts to 404).
    """
    sql = load("solar_by_structure_id")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, {"structure_id": structure_id})
        row = cur.fetchone()

    if row is None:
        return None

    return _row_to_response(row)


def fetch_solar(conn: Connection, id: int) -> SolarCacheResponse | None:
    """
    Return the solar_api_cache row for the building with the given buildings.id.
    Returns None if either the building does not exist or it has no solar cache
    entry (the router converts None to a 404).
    """
    sql = load("solar_by_building_id")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, {"id": id})
        row = cur.fetchone()

    if row is None:
        return None

    return _row_to_response(row)


def _row_to_response(row: dict[str, Any]) -> SolarCacheResponse:
    return SolarCacheResponse(
        structure_id=int(row["structure_id"]),
        address=_safe_str(row.get("address")),
        max_panels=_safe_int(row.get("max_panels")),
        max_array_area_m2=_safe_float(row.get("max_array_area_m2")),
        min_panels_kwh_annual=_safe_float(row.get("min_panels_kwh_annual")),
        max_panels_kwh_annual=_safe_float(row.get("max_panels_kwh_annual")),
        max_sunshine_hours_per_year=_safe_float(row.get("max_sunshine_hours_per_year")),
        carbon_offset_kg_per_mwh=_safe_float(row.get("carbon_offset_kg_per_mwh")),
        whole_roof_area_m2=_safe_float(row.get("whole_roof_area_m2")),
        roof_segment_stats=row.get("roof_segment_stats"),
        solar_panel_configs=row.get("solar_panel_configs"),
    )


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        import math
        f = float(value)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
