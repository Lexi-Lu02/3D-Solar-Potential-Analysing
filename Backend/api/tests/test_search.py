"""Unit tests for GET /api/v1/buildings/search."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _search_row(id: int = 1, structure_id: int = 12345, address: str = "1 Collins Street, Melbourne") -> dict:
    return {
        "id": id,
        "structure_id": structure_id,
        "lat": -37.818,
        "lng": 144.968,
        "address": address,
    }


def test_search_returns_matching_buildings(app_with_pool):
    app = app_with_pool(rows=[_search_row(), _search_row(id=2, structure_id=99, address="2 Collins Street, Melbourne")])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/search?q=Collins")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0]["id"] == 1
    assert body[0]["structure_id"] == 12345
    assert body[0]["address"] == "1 Collins Street, Melbourne"
    assert "lat" in body[0]
    assert "lng" in body[0]


def test_search_returns_empty_list_when_no_match(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/search?q=Nonexistent")

    assert resp.status_code == 200
    assert resp.json() == []


def test_search_requires_q_param(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/search")

    assert resp.status_code == 422


def test_search_q_must_be_at_least_2_chars(app_with_pool):
    app = app_with_pool(rows=[])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/search?q=a")

    assert resp.status_code == 422


def test_search_does_not_conflict_with_building_detail(app_with_pool):
    """Regression: /search must not be parsed as buildings/{id} with id='search'."""
    app = app_with_pool(rows=[_search_row()])
    with TestClient(app) as client:
        resp = client.get("/api/v1/buildings/search?q=Collins")
    # Should get 200 list, not 422 from id validation
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
