"""PG connection helper. Reads env vars / Backend/.env / falls back to defaults."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2


def _load_backend_env() -> None:
    # minimal .env parser; avoids python-dotenv dep
    backend_env = Path(__file__).resolve().parent.parent / "Backend" / ".env"
    if not backend_env.exists():
        return
    for line in backend_env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def get_connection():
    _load_backend_env()
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "15.134.87.211"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "melbourne_solar"),
        user=os.environ.get("DB_USER", "teamuser"),
        password=os.environ.get("DB_PASSWORD", "123456"),
    )
