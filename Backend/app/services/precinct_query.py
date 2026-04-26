"""Precinct query service."""

from __future__ import annotations

import json
from typing import Any, Literal

from psycopg import Connection
from psycopg.rows import dict_row

from ..models.schemas import PrecinctDetail, PrecinctSummary
from ..sql import load

SortKey = Literal["kwh", "area", "buildings", "gap"]

_SORT_FIELD: dict[str, str] = {
    "kwh": "total_kwh_annual",
    "area": "total_usable_area_m2",
    "buildings": "building_count",
    "gap": "adoption_gap_kw",
}


class PrecinctNotFound(Exception):
    def __init__(self, precinct_id: int):
        super().__init__(f"precinct {precinct_id} not found")
        self.precinct_id = precinct_id


def list_precincts(conn: Connection, sort: SortKey) -> list[PrecinctSummary]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(load("precincts_list"))
        rows = cur.fetchall()

    field = _SORT_FIELD[sort]
    rows.sort(key=lambda r: _num(r.get(field)), reverse=True)

    return [
        PrecinctSummary(
            precinct_id=int(r["precinct_id"]),
            name=str(r["name"]),
            postcode=_str(r.get("postcode")),
            total_kwh_annual=_num(r.get("total_kwh_annual")),
            total_usable_area_m2=_num(r.get("total_usable_area_m2")),
            installed_capacity_kw=_num(r.get("installed_capacity_kw")),
            potential_capacity_kw=_num(r.get("potential_capacity_kw")),
            adoption_gap_kw=_num(r.get("adoption_gap_kw")),
            building_count=int(r.get("building_count") or 0),
            rank=i + 1,
        )
        for i, r in enumerate(rows)
    ]


def fetch_precinct(conn: Connection, precinct_id: int) -> PrecinctDetail:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(load("precinct_by_id"), {"precinct_id": precinct_id})
        row = cur.fetchone()

    if row is None:
        raise PrecinctNotFound(precinct_id)

    return PrecinctDetail(
        precinct_id=int(row["precinct_id"]),
        name=str(row["name"]),
        postcode=_str(row.get("postcode")),
        total_kwh_annual=_num(row.get("total_kwh_annual")),
        total_usable_area_m2=_num(row.get("total_usable_area_m2")),
        installed_capacity_kw=_num(row.get("installed_capacity_kw")),
        potential_capacity_kw=_num(row.get("potential_capacity_kw")),
        adoption_gap_kw=_num(row.get("adoption_gap_kw")),
        building_count=int(row.get("building_count") or 0),
        geo_boundary=_geo(row.get("geo_boundary")),
        rank=None,
    )


def _num(v: Any) -> float:
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _geo(v: Any) -> dict[str, Any] | None:
    # ST_AsGeoJSON returns a string
    if v is None:
        return None
    if isinstance(v, dict):
        return v
    try:
        return json.loads(v)
    except (TypeError, ValueError):
        return None
