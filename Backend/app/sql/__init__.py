"""
SQL file loader.

Each .sql file in this package is loaded once and cached. Routers and
services call `load("building_by_id")` instead of touching the filesystem
directly, so swapping to PostGIS later means editing only the .sql files.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_SQL_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def load(name: str) -> str:
    path = _SQL_DIR / f"{name}.sql"
    if not path.is_file():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")
