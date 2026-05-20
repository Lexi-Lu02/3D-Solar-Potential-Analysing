"""
Sun position endpoints for Epic 4.

GET /api/v1/sun/path — 25 samples from 6:00-18:00 (every 0.5h)

Pure function (no DB). Frontend calls /sun/path once per date and caches results.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response

from ..models.schemas import (
    SunPathResponse,
    SunPathSample,
)
from ..services.sun_position import get_sun_position

router = APIRouter(prefix="/sun", tags=["sun"])

# responses are deterministic, cache for a year
_LONG_CACHE = "public, max-age=31536000, immutable"
_DATE_REGEX = r"^\d{4}-\d{2}-\d{2}$"
_PATH_HOURS: tuple[float, ...] = tuple(6 + 0.5 * i for i in range(25))



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


