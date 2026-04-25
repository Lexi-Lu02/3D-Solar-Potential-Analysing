"""
Liveness + DB-readiness probe.

Returns 200 with {status, db, buildings_count} when both the API process is
running and PostgreSQL is reachable. Returns 503 with the same envelope shape
(but status='error', db='unreachable') if the SELECT fails for any reason.

Cached as `no-store` so monitoring agents always see the live answer.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Response
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import HealthResponse
from ..sql import load

router = APIRouter(tags=["health"])

logger = logging.getLogger(__name__)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness + DB readiness probe",
)
def health(
    response: Response,
    conn: Connection = Depends(get_conn),
) -> HealthResponse:
    response.headers["Cache-Control"] = "no-store"
    try:
        with conn.cursor() as cur:
            cur.execute(load("buildings_count"))
            row = cur.fetchone()
            count = int(row[0]) if row else 0
    except Exception:  # pragma: no cover - exercised by integration tests
        logger.exception("Health probe failed: DB query raised")
        response.status_code = 503
        return HealthResponse(status="error", db="unreachable", buildings_count=0)

    return HealthResponse(status="ok", db="ok", buildings_count=count)
