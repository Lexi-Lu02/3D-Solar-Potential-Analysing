"""Unit tests for GET /api/v1/buildings/{id}/yield."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.constants.melbourne_psh import (
    DAYS_IN_MONTH,
    MONTHLY_PSH,
    PANEL_EFFICIENCY,
    PERFORMANCE_RATIO,
)


def _row_with_data(usable_roof_area: float = 60.0) -> dict:
    return {"id": 1, "structure_id": 12345, "usable_roof_area": usable_roof_area}


def _row_no_solar() -> dict:
    return {"id": 2, "structure_id": 99999, "usable_roof_area": None}


def test_yield_has_12_monthly_items(app_with_pool):
    app = app_with_pool(rows=[_row_with_data()])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/1/yield")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["has_data"] is True
    assert len(body["kwh_monthly"]) == 12


def test_yield_monthly_names_and_days(app_with_pool):
    app = app_with_pool(rows=[_row_with_data()])
    with TestClient(app) as client:
        body = client.get("/api/v1/buildings/1/yield").json()

    expected_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for i, item in enumerate(body["kwh_monthly"]):
        assert item["month"] == expected_names[i]
        assert item["days"] == DAYS_IN_MONTH[i]


def test_yield_kwh_annual_equals_sum_of_monthly(app_with_pool):
    app = app_with_pool(rows=[_row_with_data()])
    with TestClient(app) as client:
        body = client.get("/api/v1/buildings/1/yield").json()

    assert body["kwh_annual"] == sum(item["kwh"] for item in body["kwh_monthly"])


def test_yield_formula_spot_check(app_with_pool):
    """January: kwh = 60 × 0.20 × 0.75 × 6.56 × 31 = 1827.36 → round = 1827."""
    app = app_with_pool(rows=[_row_with_data(60.0)])
    with TestClient(app) as client:
        body = client.get("/api/v1/buildings/1/yield").json()

    jan = body["kwh_monthly"][0]
    expected = round(60.0 * PANEL_EFFICIENCY * PERFORMANCE_RATIO * MONTHLY_PSH[0] * DAYS_IN_MONTH[0])
    assert jan["kwh"] == expected


def test_yield_no_solar_data_returns_zeros(app_with_pool):
    app = app_with_pool(rows=[_row_no_solar()])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/2/yield")

    assert resp.status_code == 200
    body = resp.json()
    assert body["has_data"] is False
    assert body["kwh_annual"] == 0
    assert body["kwh_monthly"] == []


def test_yield_not_found_returns_404(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/999/yield")

    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "not_found"
    assert "999" in body["detail"]


def test_yield_assumptions_are_present(app_with_pool):
    app = app_with_pool(rows=[_row_with_data(75.0)])
    with TestClient(app) as client:
        body = client.get("/api/v1/buildings/1/yield").json()

    a = body["assumptions"]
    assert a["panel_efficiency"] == PANEL_EFFICIENCY
    assert a["performance_ratio"] == PERFORMANCE_RATIO
    assert a["usable_roof_area_m2"] == 75.0
