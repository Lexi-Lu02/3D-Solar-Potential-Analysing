"""
Sun position endpoints for Epic 4.

GET /api/v1/sun/position    — altitude/azimuth at a given date+hour
GET /api/v1/sun/path        — 25 samples from 6:00-18:00 (every 0.5h)
GET /api/v1/sun/psh-monthly — Melbourne monthly Peak Sun Hours constants

All endpoints are pure functions (no DB). Frontend can call /sun/path
once per season and cache the results in sessionStorage.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response

from ..constants.melbourne_psh import MONTHLY_PSH
from ..models.schemas import (
    PshMonthlyResponse,
    SunPathResponse,
    SunPathSample,
    SunPositionResponse,
)
from ..services.sun_position import get_sun_position

router = APIRouter(prefix="/sun", tags=["sun"])

# responses are deterministic, cache for a year
_LONG_CACHE = "public, max-age=31536000, immutable"
_DATE_REGEX = r"^\d{4}-\d{2}-\d{2}$"
_PATH_HOURS: tuple[float, ...] = tuple(6 + 0.5 * i for i in range(25))


@router.get(
    "/position",
    response_model=SunPositionResponse,
    summary="Sun altitude and azimuth at a given time (Melbourne CBD)",
)
def get_position(
    response: Response,
    date: str = Query(
        ...,
        pattern=_DATE_REGEX,
        description="Local date (YYYY-MM-DD)",
        examples=["2025-12-21"],
    ),
    hour: float = Query(
        ...,
        ge=0,
        le=24,
        description="Local time in hours, decimals allowed (e.g. 13.5 = 13:30)",
        examples=[12.0],
    ),
) -> SunPositionResponse:
    response.headers["Cache-Control"] = _LONG_CACHE
    data = get_sun_position(date, hour)
    return SunPositionResponse(**data)


@router.get(
    "/path",
    response_model=SunPathResponse,
    summary="25 sun position samples from 6:00-18:00 at 0.5h intervals",
)
def get_path(
    response: Response,
    date: str = Query(
        ...,
        pattern=_DATE_REGEX,
        description="Local date (YYYY-MM-DD)",
        examples=["2025-12-21"],
    ),
) -> SunPathResponse:
    response.headers["Cache-Control"] = _LONG_CACHE
    samples = [
        SunPathSample(hour=h, **get_sun_position(date, h))
        for h in _PATH_HOURS
    ]
    return SunPathResponse(date=date, samples=samples)


@router.get(
    "/psh-monthly",
    response_model=PshMonthlyResponse,
    summary="Melbourne monthly Peak Sun Hours constants (NASA POWER x BOM calibrated)",
)
def get_psh_monthly(response: Response) -> PshMonthlyResponse:
    # season_factor = avg(PSH for season months) / avg(PSH all year)
    # same formula as solar_impact._season_factor (Epic 6),
    # exposed here so the frontend can render a calculation breakdown.
    response.headers["Cache-Control"] = _LONG_CACHE
    psh_list = list(MONTHLY_PSH)
    return PshMonthlyResponse(
        location="Melbourne",
        psh_monthly=psh_list,
        psh_annual_avg=round(sum(psh_list) / 12, 4),
    )