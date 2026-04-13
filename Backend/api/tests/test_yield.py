"""Unit tests for GET /api/v1/buildings/{structure_id}/yield."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.constants.melbourne_psh import (
    DAYS_IN_MONTH,
    MONTHLY_PSH,
    PANEL_EFFICIENCY,
    PERFORMANCE_RATIO,
)


def _row_with_data(usable_roof_area: float = 60.0) -> dict:
    return {"structure_id": 12345, "usable_roof_area": usable_roof_area}


def _row_no_solar() -> dict:
    return {"structure_id": 99999, "usable_roof_area": None}


def test_yield_has_12_monthly_items(app_with_pool):
    app = app_with_pool(rows=[_row_with_data()])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/12345/yield")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["has_data"] is True
    assert len(body["kwh_monthly"]) == 12


def test_yield_monthly_names_and_days(app_with_pool):
    app = app_with_pool(rows=[_row_with_data()])
    with TestClient(app) as client:
        body = client.get("/api/v1/buildings/12345/yield").json()

    expected_names = ["Jan","Feb","Mar","Apr","May","Jun",
                      "Jul","Aug","Sep","Oct","Nov","Dec"]
    expected_days  = list(DAYS_IN_MONTH)

    for i, item in enumerate(body["kwh_monthly"]):
        assert item["month"] == expected_names[i], f"month mismatch at index {i}"
        assert item["days"]  == expected_days[i],  f"days mismatch at index {i}"


def test_yield_annual_equals_sum_of_monthly(app_with_pool):
    """kwh_annual 必须精确等于 kwh_monthly 的加总。"""
    app = app_with_pool(rows=[_row_with_data(60.0)])
    with TestClient(app) as client:
        body = client.get("/api/v1/buildings/12345/yield").json()

    total = sum(item["kwh"] for item in body["kwh_monthly"])
    assert body["kwh_annual"] == total


def test_yield_formula_spot_check(app_with_pool):
    """
    人工验算 1月（索引 0）：
        kwh = 60 × 0.20 × 0.75 × 6.56 × 31 = 1828.8 → round = 1829
    """
    app = app_with_pool(rows=[_row_with_data(60.0)])
    with TestClient(app) as client:
        body = client.get("/api/v1/buildings/12345/yield").json()

    jan = body["kwh_monthly"][0]
    expected_jan = round(60.0 * PANEL_EFFICIENCY * PERFORMANCE_RATIO * MONTHLY_PSH[0] * DAYS_IN_MONTH[0])
    assert jan["kwh"] == expected_jan
    assert jan["psh"] == MONTHLY_PSH[0]


def test_yield_assumptions_in_response(app_with_pool):
    app = app_with_pool(rows=[_row_with_data(60.0)])
    with TestClient(app) as client:
        body = client.get("/api/v1/buildings/12345/yield").json()

    a = body["assumptions"]
    assert a["panel_efficiency"] == PANEL_EFFICIENCY
    assert a["performance_ratio"] == PERFORMANCE_RATIO
    assert a["peak_sun_hours_annual"] == 4.1
    assert a["usable_roof_area_m2"] == 60.0


def test_yield_no_solar_data_returns_zeros(app_with_pool):
    app = app_with_pool(rows=[_row_no_solar()])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/99999/yield")

    assert resp.status_code == 200
    body = resp.json()
    assert body["has_data"] is False
    assert body["kwh_annual"] == 0
    assert body["kwh_monthly"] == []
    assert body["assumptions"]["usable_roof_area_m2"] == 0.0


def test_yield_not_found_returns_404(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/777/yield")

    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "not_found"
    assert "777" in body["detail"]


def test_yield_invalid_id_returns_422(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/0/yield")

    assert resp.status_code == 422
    assert resp.json()["error"] == "validation_error"


def test_yield_cache_header(app_with_pool):
    app = app_with_pool(rows=[_row_with_data()])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/12345/yield")

    assert "max-age" in resp.headers.get("cache-control", "")


def test_yield_annual_reasonable_for_60m2(app_with_pool):
    """
    60 m² usable area — 年度合理范围校验。
    用 4.1 PSH × 365 × 0.20 × 0.75 × 60 = 13_505 kWh 作为参考值，
    月度加总法因 PSH 缩放后的年均 ≈ 4.10，结果应在 ±2% 内。
    """
    app = app_with_pool(rows=[_row_with_data(60.0)])
    with TestClient(app) as client:
        body = client.get("/api/v1/buildings/12345/yield").json()

    reference = round(60.0 * 0.20 * 0.75 * 4.1 * 365)  # 13_505
    assert abs(body["kwh_annual"] - reference) / reference < 0.02
