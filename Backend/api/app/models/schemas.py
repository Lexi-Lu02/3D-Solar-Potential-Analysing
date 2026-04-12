"""
Pydantic response models. Adding new endpoints means adding a model here.

Why duplicate the shape vs. dumping a raw dict from psycopg:
  1. FastAPI uses these to drive /docs (Swagger UI) — they ARE the API contract
  2. They strip out any column we accidentally SELECTed but don't want exposed
  3. They give the frontend a stable shape even if the DB schema shifts
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# --- /health ------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: Literal["ok", "error"] = Field(..., description="Overall service health")
    db: Literal["ok", "unreachable"] = Field(..., description="Database connectivity")
    buildings_count: int = Field(
        ..., ge=0, description="Number of rows currently in the buildings table"
    )


# --- /buildings/{id} ----------------------------------------------------------
#
# The response is intentionally nested into small groups (location, footprint,
# height, solar) so the frontend can map each panel section to a sub-object
# without rebuilding state. The grouping also makes the OpenAPI doc easier to
# scan than a flat 18-field object.


class BuildingLocation(BaseModel):
    lat: float = Field(..., description="Latitude (WGS84)")
    lng: float = Field(..., description="Longitude (WGS84)")


class BuildingFootprint(BaseModel):
    footprint_area_m2: float = Field(
        ..., ge=0, description="Roof footprint area in square metres, computed from geo_shape"
    )
    roof_type: str | None = Field(None, description="Roof type label from City of Melbourne")
    date_captured: str | None = Field(
        None, description="ISO 8601 date the footprint was captured"
    )


class BuildingHeight(BaseModel):
    building_height_m: float = Field(..., description="Total building height (used for 3D extrusion)")
    base_height_m: float = Field(..., description="Base / ground offset")
    max_elevation_m: float = Field(..., description="Highest point elevation")
    min_elevation_m: float = Field(..., description="Lowest point elevation")


class BuildingSolar(BaseModel):
    """
    Solar suitability data from the City of Melbourne rooftop solar survey.
    All fields except `has_data` are nullable: ~5% of buildings did not match
    any solar polygon and have no survey data at all.
    """

    has_data: bool = Field(..., description="True iff this building has survey data")
    dominant_rating: str | None = Field(
        None, description="Most common patch rating: Excellent / Good / Moderate / Poor / Very Poor"
    )
    solar_score: int | None = Field(
        None, ge=0, le=100, description="Display score 0–100, derived from solar_score_avg"
    )
    solar_score_avg: float | None = Field(
        None, ge=1, le=5, description="Mean of patch ratings on the 1–5 scale"
    )
    usable_ratio: float | None = Field(
        None, ge=0, le=1, description="Fraction of total roof area rated Good or Excellent"
    )
    usable_roof_area_m2: float | None = Field(
        None, ge=0, description="Total m² of patches rated Good or Excellent"
    )
    total_roof_area_m2: float | None = Field(
        None, ge=0, description="Sum of all surveyed roof patches"
    )
    roof_patch_count: int | None = Field(
        None, ge=0, description="Number of distinct roof patches surveyed"
    )
    excellent_area_m2: float | None = Field(
        None, ge=0, description="Total m² of patches rated Excellent"
    )


class BuildingResponse(BaseModel):
    structure_id: int = Field(..., description="City of Melbourne primary key")
    geometry: dict[str, Any] | None = Field(
        None,
        description="Parsed GeoJSON Polygon (the same shape stored in buildings.geo_shape)",
    )
    location: BuildingLocation
    footprint: BuildingFootprint
    height: BuildingHeight
    solar: BuildingSolar
    address: str | None = Field(
        None,
        description=(
            "Reverse-geocoded street address. Always null until Phase D's "
            "Nominatim batch backfill lands."
        ),
    )
