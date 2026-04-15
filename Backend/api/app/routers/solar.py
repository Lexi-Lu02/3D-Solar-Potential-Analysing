"""
GET /api/v1/buildings/{id}/solar

Returns the raw solar_api_cache record for a single building, including panel
configuration details, maximum panel count, and annual kWh with full panels.
Used by Epic 1 / Epic 2 to display detailed solar potential information.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import SolarCacheResponse
from ..services.solar_query import fetch_solar

router = APIRouter(prefix="/buildings", tags=["solar"])

logger = logging.getLogger(__name__)


@router.get(
    "/{id}/solar",
    response_model=SolarCacheResponse,
    summary="Fetch solar API cache data for a building (Epic 1/2)",
    responses={
        404: {"description": "No solar cache entry exists for the given building id"},
    },
)
def get_solar(
    response: Response,
    id: int = Path(
        ...,
        ge=1,
        description="Surrogate primary key from buildings.id (positive integer)",
        examples=[1],
    ),
    conn: Connection = Depends(get_conn),
) -> SolarCacheResponse:
    response.headers["Cache-Control"] = "public, max-age=86400"

    result = fetch_solar(conn, id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no solar cache entry for building {id}",
        )
    return result
