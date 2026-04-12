"""
Shared pytest fixtures.

These tests stub out the DB pool entirely so we never need a real PostgreSQL
to run unit tests. Phase B's `test_parity.py` adds a separate integration
suite that DOES touch the real DB.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock

import pytest

# Populate the env BEFORE the app is imported, so Settings() validates.
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_pw")


class FakeCursor:
    def __init__(self, rows: list[tuple[Any, ...]] | None = None):
        self._rows = rows or []
        self.executed: list[tuple[str, Any]] = []

    def execute(self, sql: str, params: Any = None) -> None:
        self.executed.append((sql, params))

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._rows[0] if self._rows else None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return list(self._rows)

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None


class FakeConnection:
    def __init__(self, rows: list[tuple[Any, ...]] | None = None, raise_on_query: bool = False):
        self._rows = rows or []
        self._raise = raise_on_query

    def cursor(self) -> FakeCursor:
        if self._raise:
            raise RuntimeError("simulated DB failure")
        return FakeCursor(self._rows)


class FakePool:
    def __init__(self, conn: FakeConnection):
        self._conn = conn

    @contextmanager
    def connection(self):
        yield self._conn

    def open(self, *_: Any, **__: Any) -> None:
        return None

    def close(self) -> None:
        return None


@pytest.fixture
def fake_pool_factory():
    """Factory: build a FakePool with the given fetchone() rows."""

    def _factory(rows: list[tuple[Any, ...]] | None = None, raise_on_query: bool = False) -> FakePool:
        return FakePool(FakeConnection(rows=rows, raise_on_query=raise_on_query))

    return _factory


@pytest.fixture
def app_with_pool(fake_pool_factory, monkeypatch):
    """
    Build a FastAPI app whose lifespan installs a FakePool instead of touching PG.
    Use as: `client = TestClient(app_with_pool(rows=[(40951,)]))`.
    """
    from app import main as app_main  # noqa: WPS433  (import after env is set)

    def _builder(rows: list[tuple[Any, ...]] | None = None, raise_on_query: bool = False):
        pool = fake_pool_factory(rows=rows, raise_on_query=raise_on_query)

        # Patch build_pool so create_app's lifespan installs the fake.
        monkeypatch.setattr(app_main, "build_pool", lambda: pool)
        # Bypass the open/close context manager around the fake too.
        @contextmanager
        def _noop_lifespan(p):
            yield p
        monkeypatch.setattr(app_main, "lifespan_pool", _noop_lifespan)

        return app_main.create_app()

    return _builder
