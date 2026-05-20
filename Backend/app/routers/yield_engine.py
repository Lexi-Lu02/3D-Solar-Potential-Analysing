"""GET /api/v1/buildings/structure/{structure_id}/yield — monthly and annual kWh estimate"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import YieldResponse
from ..services.yield_calc import fetch_yield_by_structure_id

router = APIRouter(prefix="/buildings", tags=["yield"])


@router.get(
    "/structure/{structure_id}/yield",
    response_model=YieldResponse,
    summary="Fetch monthly and annual kWh yield by City of Melbourne structure_id (Epic 3)",
    responses={
        404: {"description": "No building found for the given structure_id"},
    },
)
def get_yield_by_structure(
    response: Response,
    structure_id: int = Path(
        ...,
        ge=1,
        description="City of Melbourne structure_id",
        examples=[1234567],
    ),
    conn: Connection = Depends(get_conn),
) -> YieldResponse:
    response.headers["Cache-Control"] = "public, max-age=86400"

    result = fetch_yield_by_structure_id(conn, structure_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no building found for structure_id {structure_id}",
        )
    return result


