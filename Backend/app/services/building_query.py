"""
Building lookup service.

The router is intentionally thin: it owns HTTP concerns (path params, status
codes, response model). Everything that talks to PostgreSQL or transforms raw
columns into the API shape lives here, so it can be unit-tested without
spinning up FastAPI.
"""

from __future__ import annotations

import logging
import math
from datetime import date, datetime
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from ..models.schemas import (
    BuildingFootprint,
    BuildingHeight,
    BuildingLocation,
    BuildingResponse,
    BuildingSearchItem,
    BuildingSolar,
)
from ..sql import load
from .geometry import parse_geo_shape

logger = logging.getLogger(__name__)


class BuildingNotFound(Exception):
    """Raised when no building exists for the given id."""

    def __init__(self, id: int):
        super().__init__(f"building {id} not found")
        self.id = id


def fetch_building(conn: Connection, id: int) -> BuildingResponse:
    """
    Look up one building by surrogate PK (buildings.id), LEFT JOINed with
    solar_api_cache (address) and rooftop_solar (solar data).

    Raises `BuildingNotFound` if the row does not exist. The router translates
    that into a 404 response.
    """
    sql = load("building_by_id")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, {"id": id})
        row = cur.fetchone()

    if row is None:
        raise BuildingNotFound(id)

    return _row_to_response(row)


def fetch_building_address(conn: Connection, structure_id: int) -> str | None:
    """
    Return the address for the given structure_id, preferring solar_api_cache.address
    and falling back to buildings.address. Returns None if not found or no address.
    """
    sql = load("building_address_by_structure_id")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, {"structure_id": structure_id})
        row = cur.fetchone()
    if row is None:
        return None
    return _safe_str(row.get("address"))


def search_buildings(conn: Connection, q: str) -> list[BuildingSearchItem]:
    """
    Return up to 20 buildings whose address matches the query string.
    The search is case-insensitive and partial (substring match).
    Only buildings with a populated address in solar_api_cache are returned.
    """
    sql = load("buildings_search")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, {"q": _escape_like(q)})
        rows = cur.fetchall()

    return [
        BuildingSearchItem(
            id=int(row["id"]),
            structure_id=int(row["structure_id"]),
            lat=_safe_float(row.get("lat")),
            lng=_safe_float(row.get("lng")),
            address=_safe_str(row.get("address")),
        )
        for row in rows
    ]


# --- internal helpers ---------------------------------------------------------


def _row_to_response(row: dict[str, Any]) -> BuildingResponse:
    """Convert a single PG dict row into a BuildingResponse."""
    geometry = parse_geo_shape(row.get("geo_shape"))

    has_solar = row.get("solar_score_avg") is not None
    solar_score_avg = _safe_float(row.get("solar_score_avg")) if has_solar else None

    return BuildingResponse(
        id=int(row["id"]),
        structure_id=int(row["structure_id"]),
        geometry=geometry,
        location=BuildingLocation(
            lat=_safe_float(row.get("lat")),
            lng=_safe_float(row.get("lng")),
        ),
        footprint=BuildingFootprint(
            roof_type=_safe_str(row.get("roof_type")),
            date_captured=_safe_date(row.get("date_captured")),
        ),
        height=BuildingHeight(
            building_height_m=_safe_float(row.get("building_height")),
            base_height_m=_safe_float(row.get("base_height")),
            max_elevation_m=_safe_float(row.get("max_elevation")),
            min_elevation_m=_safe_float(row.get("min_elevation")),
        ),
        solar=BuildingSolar(
            has_data=has_solar,
            dominant_rating=_safe_str(row.get("dominant_rating")) if has_solar else None,
            solar_score=_score_0_100(solar_score_avg) if has_solar else None,
            solar_score_avg=solar_score_avg,
            usable_ratio=_safe_float(row.get("usable_ratio")) if has_solar else None,
            usable_roof_area_m2=_safe_float(row.get("usable_roof_area")) if has_solar else None,
            total_roof_area_m2=_safe_float(row.get("total_roof_area")) if has_solar else None,
            roof_patch_count=_safe_int(row.get("roof_patch_count")) if has_solar else None,
            excellent_area_m2=_safe_float(row.get("excellent_area")) if has_solar else None,
        ),
        # Populated by scripts/reverse_geocode_addresses.py (Phase D).
        # Returns null until the batch script has run against solar_api_cache.
        address=_safe_str(row.get("address")),
    )


def _safe_float(value: Any) -> float:
    """Coerce DB numerics to float, mapping NULL/NaN/garbage to 0.0."""
    if value is None:
        return 0.0
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(f) or math.isinf(f):
        return 0.0
    return f


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _safe_date(value: Any) -> str | None:
    """Render a date as ISO 8601, accepting datetime/date/str/None."""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    return str(value)


def _score_0_100(score_1_to_5: float | None) -> int:
    """
    Map the rooftop_solar 1–5 scale to a 0–100 display score, matching
    `Data wrangling/build_geojson.py`. Returns 0 for None/out-of-range.
    """
    if score_1_to_5 is None:
        return 0
    if score_1_to_5 < 1 or score_1_to_5 > 5:
        return 0
    return round((score_1_to_5 - 1) / 4 * 100)


def _escape_like(s: str) -> str:
    """Escape LIKE/ILIKE metacharacters so user input matches literally.
    Pairs with ESCAPE '\\' in buildings_search.sql."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
