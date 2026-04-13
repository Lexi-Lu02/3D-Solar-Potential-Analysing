"""Unit tests for GET /api/v1/buildings/{structure_id}."""

from __future__ import annotations

import json
from datetime import date

from fastapi.testclient import TestClient

# A small Melbourne CBD polygon, ~10 m × ~10 m, encoded as a GeoJSON string
# the way buildings.geo_shape is stored in PG. Centred near Federation Square.
# At lat -37.818 the cosine factor is ~0.79, so 10m E-W ≈ 0.000114 deg lng,
# and 10m N-S ≈ 0.0000899 deg lat. We'll use a slightly larger polygon so the
# rounded area is unambiguous.
_LAT0 = -37.8180
_LNG0 = 144.9680
_DLAT = 0.000899   # ≈ 100 m N-S
_DLNG = 0.001137   # ≈ 100 m E-W (cos(-37.818°) ≈ 0.79)
TEST_POLYGON = {
    "type": "Polygon",
    "coordinates": [[
        [_LNG0,         _LAT0],
        [_LNG0 + _DLNG, _LAT0],
        [_LNG0 + _DLNG, _LAT0 + _DLAT],
        [_LNG0,         _LAT0 + _DLAT],
        [_LNG0,         _LAT0],
    ]],
}


def _row_with_solar() -> dict:
    return {
        "structure_id": 12345,
        "lat": _LAT0,
        "lng": _LNG0,
        "roof_type": "Flat",
        "building_height": 30.0,
        "base_height": 0.0,
        "max_elevation": 50.0,
        "min_elevation": 20.0,
        "date_captured": date(2018, 5, 28),
        "geo_shape": json.dumps(TEST_POLYGON),
        "total_roof_area": 95.0,
        "usable_roof_area": 60.0,
        "dominant_rating": "Good",
        "solar_score_avg": 4.0,
        "roof_patch_count": 5,
        "excellent_area": 10.0,
        "usable_ratio": 0.632,
    }


def _row_without_solar() -> dict:
    row = _row_with_solar()
    row["structure_id"] = 99999
    row["total_roof_area"] = None
    row["usable_roof_area"] = None
    row["dominant_rating"] = None
    row["solar_score_avg"] = None
    row["roof_patch_count"] = None
    row["excellent_area"] = None
    row["usable_ratio"] = None
    return row


def test_building_found_with_solar_data(app_with_pool):
    app = app_with_pool(rows=[_row_with_solar()])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/12345")

    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["structure_id"] == 12345
    assert body["address"] is None  # Phase D will populate

    # Geometry round-trips intact
    assert body["geometry"]["type"] == "Polygon"
    assert len(body["geometry"]["coordinates"][0]) == 5

    # Location
    assert body["location"]["lat"] == _LAT0
    assert body["location"]["lng"] == _LNG0

    # Footprint area: ~100 m × ~100 m polygon should be ~10_000 m² ± 1%
    fp = body["footprint"]
    assert 9_900 <= fp["footprint_area_m2"] <= 10_100
    assert fp["roof_type"] == "Flat"
    assert fp["date_captured"] == "2018-05-28"

    # Height
    h = body["height"]
    assert h["building_height_m"] == 30.0
    assert h["base_height_m"] == 0.0
    assert h["max_elevation_m"] == 50.0
    assert h["min_elevation_m"] == 20.0

    # Solar
    s = body["solar"]
    assert s["has_data"] is True
    assert s["dominant_rating"] == "Good"
    assert s["solar_score_avg"] == 4.0
    # (4.0 - 1) / 4 * 100 = 75
    assert s["solar_score"] == 75
    assert s["usable_ratio"] == 0.632
    assert s["usable_roof_area_m2"] == 60.0
    assert s["total_roof_area_m2"] == 95.0
    assert s["roof_patch_count"] == 5
    assert s["excellent_area_m2"] == 10.0

    # Cache header so the frontend / nginx can cache aggressively
    assert "max-age" in resp.headers.get("cache-control", "")


def test_building_found_without_solar_data(app_with_pool):
    app = app_with_pool(rows=[_row_without_solar()])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/99999")

    assert resp.status_code == 200, resp.text
    body = resp.json()

    s = body["solar"]
    assert s["has_data"] is False
    assert s["dominant_rating"] is None
    assert s["solar_score"] is None
    assert s["solar_score_avg"] is None
    assert s["usable_ratio"] is None
    assert s["usable_roof_area_m2"] is None
    assert s["total_roof_area_m2"] is None
    assert s["roof_patch_count"] is None
    assert s["excellent_area_m2"] is None

    # Other sections still populated
    assert body["height"]["building_height_m"] == 30.0
    assert body["footprint"]["footprint_area_m2"] > 0


def test_building_not_found_returns_404(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/777")

    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "not_found"
    assert "777" in body["detail"]
    assert "request_id" in body


def test_building_id_must_be_positive(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/0")

    assert resp.status_code == 422  # FastAPI validation, ge=1
    body = resp.json()
    assert body["error"] == "validation_error"


def test_building_id_must_be_integer(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/not-a-number")

    assert resp.status_code == 422
    body = resp.json()
    assert body["error"] == "validation_error"


def test_health_still_passes_after_buildings_router_added(app_with_pool):
    """Regression: adding the buildings router didn't break /health."""
    app = app_with_pool(rows=[(40951,)])
    with TestClient(app) as client:
        resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["buildings_count"] == 40951
