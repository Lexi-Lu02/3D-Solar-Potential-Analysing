"""GET /api/v1/precincts, /api/v1/precincts/{id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import PrecinctDetail, PrecinctListResponse
from ..services.precinct_query import (
    PrecinctNotFound,
    fetch_precinct,
    list_precincts,
)

router = APIRouter(prefix="/precincts", tags=["precincts"])


@router.get(
    "",
    response_model=PrecinctListResponse,
    summary="List all precincts, sorted by a specified metric.",
)
def get_precincts(
    response: Response,
    sort: str = Query("kwh", pattern="^(kwh|area|buildings|gap)$"),
    conn: Connection = Depends(get_conn),
) -> PrecinctListResponse:
    response.headers["Cache-Control"] = "public, max-age=3600"
    return PrecinctListResponse(sort=sort, precincts=list_precincts(conn, sort))


@router.get(
    "/{precinct_id}",
    response_model=PrecinctDetail,
    summary="Single precinct details (including GeoJSON boundaries)",
)
def get_precinct(
    response: Response,
    precinct_id: int = Path(..., ge=1),
    conn: Connection = Depends(get_conn),
) -> PrecinctDetail:
    response.headers["Cache-Control"] = "public, max-age=3600"
    try:
        return fetch_precinct(conn, precinct_id)
    except PrecinctNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"precinct {exc.precinct_id} not found",
        )
