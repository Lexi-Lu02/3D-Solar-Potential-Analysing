"""Unit tests for GET /api/v1/buildings/{id}/solar."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _solar_row(structure_id: int = 12345) -> dict:
    return {
        "structure_id": structure_id,
        "address": "1 Collins Street, Melbourne",
        "max_panels": 42,
        "max_array_area_m2": 84.0,
        "max_panels_kwh_annual": 15000.0,
        "max_sunshine_hours_per_year": 1496.5,
        "carbon_offset_kg_per_mwh": 0.79,
        "whole_roof_area_m2": 120.0,
        "roof_segment_stats": {"segments": 3},
        "solar_panel_configs": {"configs": []},
        # extra columns returned by sac.* that are not in SolarCacheResponse
        # are silently ignored by Pydantic
        "api_building_name": "Test Building",
        "center_lat": -37.818,
        "center_lng": 144.968,
        "postal_code": "3000",
        "administrative_area": "Melbourne",
        "region_code": "VIC",
        "imagery_quality": "HIGH",
        "imagery_date": None,
        "imagery_processed_date": None,
        "panel_capacity_watts": 400.0,
        "panel_height_m": 1.65,
        "panel_width_m": 1.0,
        "panel_lifetime_years": 25,
        "whole_roof_ground_area_m2": 110.0,
        "whole_roof_sunshine_quantiles": None,
        "fetched_at": None,
        "updated_at": None,
    }


def test_solar_found_returns_200(app_with_pool):
    app = app_with_pool(rows=[_solar_row()])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/1/solar")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["structure_id"] == 12345
    assert body["max_panels"] == 42
    assert body["max_array_area_m2"] == 84.0
    assert body["max_panels_kwh_annual"] == 15000.0
    assert body["address"] == "1 Collins Street, Melbourne"
    assert body["roof_segment_stats"] == {"segments": 3}
    assert "max-age" in resp.headers.get("cache-control", "")


def test_solar_not_found_returns_404(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/999/solar")

    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "not_found"
    assert "999" in body["detail"]


def test_solar_id_must_be_positive(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/0/solar")

    assert resp.status_code == 422
