"""Approximate rooftop shadow coverage from nearby building footprints."""

from __future__ import annotations

import math
from typing import Any, Literal

from psycopg import Connection
from psycopg.rows import dict_row

from ..models.schemas import ShadowImpactResponse
from ..sql import load
from .geometry import parse_geo_shape, polygon_area_m2
from .sun_position import get_sun_position

ImpactLevel = Literal["Low", "Moderate", "High"]

_SEARCH_RADIUS_M = 260
_SAMPLE_STEPS = 18
_METRES_PER_DEG_LAT = 111_320


class BuildingNotFoundForShadow(Exception):
    def __init__(self, structure_id: int):
        super().__init__(f"building structure_id {structure_id} not found")
        self.structure_id = structure_id


def fetch_shadow_impact(
    conn: Connection,
    structure_id: int,
    date: str,
    hour: float,
) -> ShadowImpactResponse:
    rows = _fetch_shadow_context(conn, structure_id)
    if not rows:
        raise BuildingNotFoundForShadow(structure_id)

    target = next((row for row in rows if row.get("is_target")), None)
    if target is None:
        raise BuildingNotFoundForShadow(structure_id)

    return compute_shadow_impact(rows, target, structure_id, date, hour)


def compute_shadow_impact(
    rows: list[dict[str, Any]],
    target: dict[str, Any],
    structure_id: int,
    date: str,
    hour: float,
) -> ShadowImpactResponse:
    receiver_geom = parse_geo_shape(target.get("geo_shape"))
    receiver_ring = _main_outer_ring(receiver_geom)
    if not receiver_ring:
        return _empty_response(structure_id, date, hour)

    sun = get_sun_position(date, hour)
    receiver_height = _effective_height(target)
    receiver_box = _bbox_from_ring(receiver_ring)
    shadow_rings: list[list[list[float]]] = []

    for row in rows:
        if row.get("is_target"):
            continue

        caster_geom = parse_geo_shape(row.get("geo_shape"))
        caster_ring = _main_outer_ring(caster_geom)
        if not caster_ring:
            continue

        shadow_ring = _build_shadow_ring(caster_ring, _effective_height(row), receiver_height, sun)
        if not shadow_ring:
            continue
        if not _bbox_intersects(receiver_box, _bbox_from_ring(shadow_ring)):
            continue
        if _polygon_may_intersect(receiver_ring, shadow_ring):
            shadow_rings.append(shadow_ring)

    shadowed, total, overlay_features = _estimate_shadowed_samples(receiver_ring, shadow_rings, receiver_height)
    coverage = round((shadowed / total) * 100, 1) if total else 0.0
    usable_area = _usable_roof_area(target, receiver_geom)
    unobstructed_area = round(usable_area * max(0.0, 1 - coverage / 100), 1) if usable_area is not None else None

    return ShadowImpactResponse(
        structure_id=structure_id,
        date=date,
        hour=hour,
        shadow_coverage_pct=coverage,
        shadowed_samples=shadowed,
        total_samples=total,
        shadow_caster_count=len(shadow_rings),
        usable_roof_area_m2=usable_area,
        unobstructed_usable_area_m2=unobstructed_area,
        overlay_geojson={
            "type": "FeatureCollection",
            "features": overlay_features,
        },
        impact=_impact_from_coverage(coverage),
        approximate=True,
    )


def _fetch_shadow_context(conn: Connection, structure_id: int) -> list[dict[str, Any]]:
    lat_delta = _SEARCH_RADIUS_M / _METRES_PER_DEG_LAT
    lng_delta = lat_delta / math.cos(math.radians(-37.8136))

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            load("buildings_shadow_context_by_structure_id"),
            {
                "structure_id": structure_id,
                "lat_delta": lat_delta,
                "lng_delta": lng_delta,
            },
        )
        return list(cur.fetchall())


def _empty_response(structure_id: int, date: str, hour: float) -> ShadowImpactResponse:
    return ShadowImpactResponse(
        structure_id=structure_id,
        date=date,
        hour=hour,
        shadow_coverage_pct=0.0,
        shadowed_samples=0,
        total_samples=0,
        shadow_caster_count=0,
        usable_roof_area_m2=None,
        unobstructed_usable_area_m2=None,
        overlay_geojson={
            "type": "FeatureCollection",
            "features": [],
        },
        impact="Low",
        approximate=True,
    )


def _main_outer_ring(geometry: dict[str, Any] | None) -> list[list[float]] | None:
    if not geometry:
        return None
    try:
        if geometry.get("type") == "Polygon":
            return geometry["coordinates"][0]
        if geometry.get("type") == "MultiPolygon":
            return geometry["coordinates"][0][0]
    except (KeyError, TypeError, IndexError):
        return None
    return None


def _effective_height(row: dict[str, Any]) -> float:
    explicit = _safe_float(row.get("building_height"))
    if explicit > 0:
        return explicit

    base = _safe_float(row.get("base_height"))
    max_elevation = _safe_float(row.get("max_elevation"))
    if max_elevation > base:
        return max_elevation - base

    return 20.0


def _usable_roof_area(row: dict[str, Any], geometry: dict[str, Any] | None) -> float | None:
    usable = _safe_float(row.get("usable_roof_area"))
    if usable > 0:
        return round(usable, 1)

    footprint = polygon_area_m2(geometry)
    return round(footprint, 1) if footprint > 0 else None


def _build_shadow_ring(
    caster_ring: list[list[float]],
    caster_height: float,
    receiver_height: float,
    sun: dict[str, Any],
) -> list[list[float]] | None:
    altitude = _safe_float(sun.get("altitude_deg"))
    if altitude <= 0:
        return None

    height_diff = max(0.0, caster_height - receiver_height)
    if height_diff <= 0:
        return None

    tan_altitude = math.tan(math.radians(altitude))
    shadow_length = caster_height * 8 if tan_altitude <= 0.01 else min(height_diff / tan_altitude, caster_height * 8)
    if shadow_length <= 0:
        return None

    shadow_azimuth = (_safe_float(sun.get("azimuth_deg")) + 180) % 360
    rad = math.radians(shadow_azimuth)
    dx_m = math.sin(rad) * shadow_length
    dy_m = math.cos(rad) * shadow_length
    shifted = [_shift_lng_lat(lng, lat, dx_m, dy_m) for lng, lat in caster_ring]

    return [*caster_ring, *reversed(shifted), caster_ring[0]]


def _estimate_shadowed_samples(
    receiver_ring: list[list[float]],
    shadow_rings: list[list[list[float]]],
    roof_height: float,
) -> tuple[int, int, list[dict[str, Any]]]:
    box = _bbox_from_ring(receiver_ring)
    roof_samples = 0
    shaded_samples = 0
    overlay_features: list[dict[str, Any]] = []
    cell_lng = (box["max_lng"] - box["min_lng"]) / _SAMPLE_STEPS
    cell_lat = (box["max_lat"] - box["min_lat"]) / _SAMPLE_STEPS

    for x in range(_SAMPLE_STEPS):
        for y in range(_SAMPLE_STEPS):
            lng = box["min_lng"] + ((x + 0.5) / _SAMPLE_STEPS) * (box["max_lng"] - box["min_lng"])
            lat = box["min_lat"] + ((y + 0.5) / _SAMPLE_STEPS) * (box["max_lat"] - box["min_lat"])
            point = [lng, lat]

            if not _point_in_ring(point, receiver_ring):
                continue

            roof_samples += 1
            shaded = any(_point_in_ring(point, ring) for ring in shadow_rings)
            if shaded:
                shaded_samples += 1
            overlay_features.append(_sample_cell_feature(lng, lat, cell_lng, cell_lat, shaded, roof_height))

    return shaded_samples, roof_samples, overlay_features


def _sample_cell_feature(
    lng: float,
    lat: float,
    cell_lng: float,
    cell_lat: float,
    shaded: bool,
    roof_height: float,
) -> dict[str, Any]:
    half_lng = cell_lng * 0.42
    half_lat = cell_lat * 0.42
    ring = [
        [lng - half_lng, lat - half_lat],
        [lng + half_lng, lat - half_lat],
        [lng + half_lng, lat + half_lat],
        [lng - half_lng, lat + half_lat],
        [lng - half_lng, lat - half_lat],
    ]

    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [ring],
        },
        "properties": {
            "kind": "rooftop-shaded" if shaded else "rooftop-unobstructed",
            "roof_height": roof_height,
        },
    }


def _polygon_may_intersect(receiver_ring: list[list[float]], shadow_ring: list[list[float]]) -> bool:
    if not _bbox_intersects(_bbox_from_ring(receiver_ring), _bbox_from_ring(shadow_ring)):
        return False

    center = _ring_center(receiver_ring)
    if center and _point_in_ring(center, shadow_ring):
        return True

    return any(_point_in_ring(point, shadow_ring) for point in receiver_ring)


def _bbox_from_ring(ring: list[list[float]]) -> dict[str, float]:
    lngs = [point[0] for point in ring]
    lats = [point[1] for point in ring]
    return {
        "min_lng": min(lngs),
        "min_lat": min(lats),
        "max_lng": max(lngs),
        "max_lat": max(lats),
    }


def _bbox_intersects(a: dict[str, float], b: dict[str, float]) -> bool:
    return not (
        a["max_lng"] < b["min_lng"]
        or a["min_lng"] > b["max_lng"]
        or a["max_lat"] < b["min_lat"]
        or a["min_lat"] > b["max_lat"]
    )


def _point_in_ring(point: list[float], ring: list[list[float]]) -> bool:
    px, py = point
    inside = False
    j = len(ring) - 1

    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        intersects = ((yi > py) != (yj > py)) and (
            px < ((xj - xi) * (py - yi)) / ((yj - yi) + 0.0000000001) + xi
        )
        if intersects:
            inside = not inside
        j = i

    return inside


def _ring_center(ring: list[list[float]]) -> list[float] | None:
    if not ring:
        return None
    return [
        sum(point[0] for point in ring) / len(ring),
        sum(point[1] for point in ring) / len(ring),
    ]


def _shift_lng_lat(lng: float, lat: float, dx_m: float, dy_m: float) -> list[float]:
    d_lat = dy_m / _METRES_PER_DEG_LAT
    d_lng = dx_m / (_METRES_PER_DEG_LAT * math.cos(math.radians(lat)))
    return [lng + d_lng, lat + d_lat]


def _impact_from_coverage(coverage: float) -> ImpactLevel:
    if coverage < 10:
        return "Low"
    if coverage < 35:
        return "Moderate"
    return "High"


def _safe_float(value: Any) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(f) or math.isinf(f):
        return 0.0
    return f
