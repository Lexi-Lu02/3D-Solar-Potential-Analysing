"""
GET /api/v1/buildings/{structure_id}

Returns one building's geometry, height, footprint, and solar suitability —
everything Epic 2's "Building Details Panel" needs **except** the kWh
breakdown, which lives at GET /api/v1/buildings/{structure_id}/yield (Phase C).
The split keeps each response small and lets the frontend cache the two
independently.

Designed to be extended later with bbox / batch lookups (Epic 1's bulk load),
but those are deliberately out of scope until the frontend asks for them.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response, status
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import BuildingResponse
from ..services.building_query import BuildingNotFound, fetch_building

router = APIRouter(prefix="/buildings", tags=["buildings"])

logger = logging.getLogger(__name__)


@router.get(
    "/{structure_id}",
    response_model=BuildingResponse,
    summary="Fetch a single building by City of Melbourne structure_id",
    responses={
        404: {"description": "No building exists with the given structure_id"},
    },
)
def get_building(
    request: Request,
    response: Response,
    structure_id: int = Path(
        ...,
        ge=1,
        description="City of Melbourne structure_id (positive integer)",
        examples=[12345],
    ),
    conn: Connection = Depends(get_conn),
) -> BuildingResponse:
    # Static rows for the lifetime of the data wrangling output. Cache
    # aggressively at the edge so repeated panel opens cost zero DB hits.
    response.headers["Cache-Control"] = "public, max-age=86400"

    try:
        return fetch_building(conn, structure_id)
    except BuildingNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"building {exc.structure_id} not found",
        )
