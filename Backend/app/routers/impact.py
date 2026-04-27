"""GET /api/v1/buildings/{id}/impact"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import ImpactResponse
from ..services.solar_impact import BuildingNotFoundForImpact, fetch_impact

router = APIRouter(prefix="/buildings", tags=["impact"])


@router.get(
    "/{id}/impact",
    response_model=ImpactResponse,
    summary="Financial + environmental impact for one building (Epic 6)",
    responses={404: {"description": "Building has no cached solar data"}},
)
def get_building_impact(
    response: Response,
    id: int = Path(..., ge=1),
    season: str = Query(
        "annual",
        pattern="^(annual|summer|autumn|winter|spring)$",
    ),
    conn: Connection = Depends(get_conn),
) -> ImpactResponse:
    # Inputs are static for the lifetime of solar_api_cache; cache hard.
    response.headers["Cache-Control"] = "public, max-age=86400"
    try:
        return fetch_impact(conn, id, season)  # type: ignore[arg-type]
    except BuildingNotFoundForImpact as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"building {exc.id} not found",
        )
