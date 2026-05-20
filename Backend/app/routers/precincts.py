"""GET /api/v1/precincts — list all precincts sorted by a specified metric"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import PrecinctListResponse
from ..services.precinct_query import list_precincts

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


