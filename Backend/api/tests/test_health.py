"""Unit tests for GET /api/v1/health."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok_with_count(app_with_pool):
    app = app_with_pool(rows=[(40951,)])
    with TestClient(app) as client:
        resp = client.get("/api/v1/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "db": "ok", "buildings_count": 40951}
    assert resp.headers.get("cache-control") == "no-store"
    assert "x-request-id" in resp.headers


def test_health_returns_503_when_db_unreachable(app_with_pool):
    app = app_with_pool(raise_on_query=True)
    with TestClient(app) as client:
        resp = client.get("/api/v1/health")

    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "error"
    assert body["db"] == "unreachable"
    assert body["buildings_count"] == 0
