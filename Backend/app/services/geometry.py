"""
Polygon geometry helpers.

The DB stores `buildings.geo_shape` as a GeoJSON Polygon string (no PostGIS).
We need:
  1. The 2D footprint area in square metres — used by /buildings/{id} and as
     the basis for /yield's energy estimate.
  2. The parsed GeoJSON object — handed back to the frontend as-is so MapLibre
     can render it.

The area calculation mirrors `Data wrangling/build_geojson.py::polygon_area_m2`
exactly, so the API and the static GeoJSON pipeline produce identical numbers.
This lets the Phase F frontend migration ship without spec drift.
"""

from __future__ import annotations

import json
import math
from typing import Any

# Earth radius (mean) in metres — same value used by the data wrangling script.
_EARTH_RADIUS_M = 6_371_000
_LAT_SCALE = math.pi * _EARTH_RADIUS_M / 180  # metres per degree of latitude


def parse_geo_shape(geo_shape: str | dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Accept either a GeoJSON string (as stored in PG) or an already-parsed dict.
    Returns the dict, or None if input is missing/unparseable.
    """
    if geo_shape is None:
        return None
    if isinstance(geo_shape, dict):
        return geo_shape
    try:
        return json.loads(geo_shape)
    except (TypeError, ValueError):
        return None


def polygon_area_m2(geo_shape: str | dict[str, Any] | None) -> float:
    """
    Compute the 2D footprint area of a GeoJSON Polygon in square metres.

    Uses the spherical shoelace formula with a local equirectangular projection
    centred on the polygon centroid latitude. Accurate to ~0.1% for
    building-scale polygons anywhere in Melbourne.

    Returns 0.0 for any input that fails to parse — callers can treat 0 as
    "unknown" without needing to handle exceptions. This matches the existing
    pipeline's behaviour.
    """
    geom = parse_geo_shape(geo_shape)
    if geom is None:
        return 0.0

    try:
        coords = geom["coordinates"][0]  # outer ring only
    except (KeyError, TypeError, IndexError):
        return 0.0

    if len(coords) < 3:
        return 0.0

    lats = [c[1] for c in coords]
    lat0 = sum(lats) / len(lats)
    lng_scale = _LAT_SCALE * math.cos(math.radians(lat0))

    area = 0.0
    n = len(coords)
    for i in range(n - 1):
        x1 = coords[i][0] * lng_scale
        y1 = coords[i][1] * _LAT_SCALE
        x2 = coords[i + 1][0] * lng_scale
        y2 = coords[i + 1][1] * _LAT_SCALE
        area += x1 * y2 - x2 * y1

    return round(abs(area) / 2, 1)
