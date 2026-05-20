"""GET /api/v1/buildings/structure/{structure_id}/solar — solar API cache data"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import SolarCacheResponse
from ..services.solar_query import fetch_solar_by_structure_id

router = APIRouter(prefix="/buildings", tags=["solar"])


@router.get(
    "/structure/{structure_id}/solar",
    response_model=SolarCacheResponse,
    summary="Fetch solar API cache data for a building by City of Melbourne structure_id",
    responses={
        404: {"description": "No solar cache entry for the given structure_id"},
    },
)
def get_solar_by_structure(
    response: Response,
    structure_id: int = Path(
        ...,
        ge=1,
        description="City of Melbourne structure_id",
        examples=[1234567],
    ),
    conn: Connection = Depends(get_conn),
) -> SolarCacheResponse:
    response.headers["Cache-Control"] = "public, max-age=86400"

    result = fetch_solar_by_structure_id(conn, structure_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no solar cache entry for structure_id {structure_id}",
        )
    return result


