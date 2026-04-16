"""
GET /api/v1/buildings/search   — address search (must be registered before /{id})
GET /api/v1/buildings/{id}     — single building detail

Returns one building's geometry, height, footprint, and solar suitability —
everything Epic 2's "Building Details Panel" needs except the kWh breakdown,
which lives at GET /api/v1/buildings/{id}/yield.

The /search route must be declared before /{id} so FastAPI does not try to
parse the literal string "search" as an integer path parameter.
"""

from __future__ import annotations

import logging

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response, status
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import BuildingAddressItem, BuildingResponse, BuildingSearchItem
from ..services.building_query import BuildingNotFound, fetch_building, fetch_building_address, search_buildings

router = APIRouter(prefix="/buildings", tags=["buildings"])
logger = logging.getLogger(__name__)


@router.get(
    "/search",
    response_model=list[BuildingSearchItem],
    summary="Search buildings by address (partial, case-insensitive)",
    responses={
        200: {"description": "List of matching buildings (empty list if none match)"},
    },
)
def get_buildings_search(
    response: Response,
    q: str = Query(
        ...,
        min_length=2,
        max_length=200,
        description="Address search string — matched with ILIKE %q%",
        examples=["Collins"],
    ),
    conn: Connection = Depends(get_conn),
) -> list[BuildingSearchItem]:
    response.headers["Cache-Control"] = "public, max-age=300"
    try:
        return search_buildings(conn, q)
    except Exception as exc:
        logger.exception("search_buildings failed for q=%r: %s", q, exc)
        raise HTTPException(status_code=503, detail="Search temporarily unavailable")


@router.get(
    "/by-structure/{structure_id}/address",
    response_model=BuildingAddressItem,
    summary="Fetch the street address for a building by City of Melbourne structure_id",
    responses={
        200: {"description": "Address for the building (may be null if not yet geocoded)"},
    },
)
def get_building_address_by_structure(
    response: Response,
    structure_id: int = Path(
        ...,
        ge=1,
        description="City of Melbourne structure_id",
        examples=[1234567],
    ),
    conn: Connection = Depends(get_conn),
) -> BuildingAddressItem:
    response.headers["Cache-Control"] = "public, max-age=86400"
    address = fetch_building_address(conn, structure_id)
    return BuildingAddressItem(structure_id=structure_id, address=address)


@router.get(
    "/{id}",
    response_model=BuildingResponse,
    summary="Fetch a single building by surrogate primary key (buildings.id)",
    responses={
        404: {"description": "No building exists with the given id"},
    },
)
def get_building(
    request: Request,
    response: Response,
    id: int = Path(
        ...,
        ge=1,
        description="Surrogate primary key from buildings.id (positive integer)",
        examples=[1],
    ),
    conn: Connection = Depends(get_conn),
) -> BuildingResponse:
    # Static rows for the lifetime of the data wrangling output. Cache
    # aggressively at the edge so repeated panel opens cost zero DB hits.
    response.headers["Cache-Control"] = "public, max-age=86400"

    try:
        return fetch_building(conn, id)
    except BuildingNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"building {exc.id} not found",
        )
