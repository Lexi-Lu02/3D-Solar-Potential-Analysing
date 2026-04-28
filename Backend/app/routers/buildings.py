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

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response, status
from psycopg import Connection

from ..db import get_conn
from ..models.schemas import (
    BuildingAddressItem,
    BuildingResponse,
    BuildingSearchItem,
    BuildingStatsResponse,
    ShadowImpactResponse,
)
from ..services.building_query import BuildingNotFound, fetch_building, fetch_building_address, search_buildings
from ..services.shadow_impact import BuildingNotFoundForShadow, fetch_shadow_impact
from ..sql import load

router = APIRouter(prefix="/buildings", tags=["buildings"])
logger = logging.getLogger(__name__)


@router.get(
    "/stats",
    response_model=BuildingStatsResponse,
    summary="Aggregate solar statistics across all buildings",
)
def get_buildings_stats(
    response: Response,
    conn: Connection = Depends(get_conn),
) -> BuildingStatsResponse:
    response.headers["Cache-Control"] = "public, max-age=3600"
    with conn.cursor() as cur:
        cur.execute(load("buildings_stats"))
        row = cur.fetchone()
    return BuildingStatsResponse(
        total_buildings=int(row[0] or 0),
        usable_area_m2=float(row[1] or 0),
        kwh_annual=float(row[2] or 0),
        high_potential_count=int(row[3] or 0),
    )


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
    "/by-structure/{structure_id}/shadow-impact",
    response_model=ShadowImpactResponse,
    summary="Estimate selected rooftop shadow coverage from nearby buildings",
    responses={
        404: {"description": "No building exists with the given structure_id"},
    },
)
def get_building_shadow_impact_by_structure(
    response: Response,
    structure_id: int = Path(
        ...,
        ge=1,
        description="City of Melbourne structure_id",
        examples=[1234567],
    ),
    date: str = Query(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Local simulation date (YYYY-MM-DD)",
        examples=["2025-12-21"],
    ),
    hour: float = Query(
        ...,
        ge=0,
        le=24,
        description="Local time in hours, e.g. 13.5 for 13:30",
        examples=[12.0],
    ),
    conn: Connection = Depends(get_conn),
) -> ShadowImpactResponse:
    response.headers["Cache-Control"] = "public, max-age=300"
    try:
        return fetch_shadow_impact(conn, structure_id, date, hour)
    except BuildingNotFoundForShadow as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"building structure_id {exc.structure_id} not found",
        )


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
