"""
Pydantic response models. Adding new endpoints means adding a model here.

Why duplicate the shape vs. dumping a raw dict from psycopg:
  1. FastAPI uses these to drive /docs (Swagger UI) — they ARE the API contract
  2. They strip out any column we accidentally SELECTed but don't want exposed
  3. They give the frontend a stable shape even if the DB schema shifts
"""

from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, Field


# --- /buildings/stats ---------------------------------------------------------


class BuildingStatsResponse(BaseModel):
    total_buildings: int = Field(..., ge=0, description="Total number of buildings with data")
    usable_area_m2: float = Field(..., ge=0, description="Total usable rooftop area (m²)")
    kwh_annual: float = Field(..., ge=0, description="Estimated annual solar yield (kWh)")
    high_potential_count: int = Field(..., ge=0, description="Buildings with solar score ≥ 60")


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
    id: int = Field(..., description="Surrogate primary key (buildings.id)")
    structure_id: int = Field(..., description="City of Melbourne structure_id")
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
            "Reverse-geocoded street address. Populated from solar_api_cache.address "
            "after scripts/reverse_geocode_addresses.py has run."
        ),
    )


# --- /buildings/by-structure/{structure_id}/address --------------------------


class BuildingAddressItem(BaseModel):
    structure_id: int = Field(..., description="City of Melbourne structure_id")
    address: str | None = Field(None, description="Street address (from solar_api_cache or buildings)")


# --- /buildings/search -------------------------------------------------------


class BuildingSearchItem(BaseModel):
    id: int = Field(..., description="Surrogate primary key (buildings.id)")
    structure_id: int = Field(..., description="City of Melbourne structure_id")
    lat: float = Field(..., description="Latitude (WGS84)")
    lng: float = Field(..., description="Longitude (WGS84)")
    address: str | None = Field(None, description="Street address from solar_api_cache")


# --- /buildings/{id}/solar ---------------------------------------------------


class SolarCacheResponse(BaseModel):
    """
    Raw solar API cache data from solar_api_cache for a single building.
    Used by Epic 1 / Epic 2 panels that need panel configuration details.
    """

    structure_id: int = Field(..., description="City of Melbourne structure_id")
    address: str | None = Field(None, description="Reverse-geocoded street address")
    max_panels: int | None = Field(None, ge=0, description="Maximum number of panels that fit")
    max_array_area_m2: float | None = Field(None, ge=0, description="Area covered by max panels (m²)")
    min_panels_kwh_annual: float | None = Field(
        None, ge=0, description="Annual kWh with minimum panel count"
    )
    max_panels_kwh_annual: float | None = Field(
        None, ge=0, description="Annual kWh with maximum panel count"
    )
    max_sunshine_hours_per_year: float | None = Field(
        None, ge=0, description="Max annual sunshine hours from solar API"
    )
    carbon_offset_kg_per_mwh: float | None = Field(
        None, ge=0, description="Carbon offset factor (kg CO₂ per MWh)"
    )
    whole_roof_area_m2: float | None = Field(None, ge=0, description="Total roof area from solar API (m²)")
    roof_segment_stats: Union[list, dict, None] = Field(None, description="Per-segment solar statistics (jsonb)")
    solar_panel_configs: Union[list, dict, None] = Field(None, description="Panel configuration options (jsonb)")
    panel_capacity_watts: float | None = Field(None, ge=0, description="Rated capacity of each panel in watts")


# --- /buildings/{id}/yield ---------------------------------------------------


class YieldMonthlyItem(BaseModel):
    month: str = Field(..., description="Month abbreviation, e.g. 'Jan'")
    days: int = Field(..., ge=28, le=31, description="Number of days in the month")
    psh: float = Field(..., ge=0, description="Average daily peak sun hours for the month (kWh/m²/day), from NASA POWER")
    kwh: int = Field(..., ge=0, description="Estimated electricity output for the month (kWh), rounded to integer")


class YieldAssumptions(BaseModel):
    """Parameters used in the kWh estimate, exposed so the frontend can show calculation details."""

    panel_efficiency: float = Field(
        ..., description="Panel conversion efficiency, fixed at 0.20 (20%)"
    )
    performance_ratio: float = Field(
        ..., description="System performance ratio (inverter losses etc.), fixed at 0.75"
    )
    peak_sun_hours_annual: float = Field(
        ..., description="Annual average peak sun hours calibrated to BOM station 086338 (4.1 PSH/day)"
    )
    usable_roof_area_m2: float = Field(
        ..., ge=0, description="Usable roof area used in the calculation (m²), from the rooftop_solar survey"
    )


class YieldResponse(BaseModel):
    structure_id: int = Field(..., description="City of Melbourne structure_id")
    has_data: bool = Field(
        ..., description="True if solar survey data exists. When False, kwh_annual=0 and kwh_monthly=[]"
    )
    kwh_annual: int = Field(
        ..., ge=0,
        description="Estimated annual electricity output (kWh), equals sum(kwh_monthly)"
    )
    kwh_monthly: list[YieldMonthlyItem] = Field(
        ..., description="Monthly breakdown for all 12 months (empty list when has_data=False)"
    )
    solar_score_avg: float | None = Field(
        None, ge=1, le=5,
        description="Mean patch rating on the 1–5 survey scale. NULL when no rooftop_solar record exists."
    )
    assumptions: YieldAssumptions = Field(
        ..., description="Parameters used in this calculation, for transparent display in the frontend"
    )


# --- /sun/* (Epic 4 — Sun/Shadow) -------------------------------------------


class SunPositionResponse(BaseModel):
    """Sun altitude and azimuth at a given time, Melbourne CBD."""

    altitude_deg: float = Field(
        ..., ge=0, le=90,
        description="Solar altitude in degrees. 0 when below horizon."
    )
    azimuth_deg: float = Field(
        ..., ge=0, lt=360,
        description="Solar azimuth in degrees. N=0, clockwise."
    )
    shadow_factor: float | None = Field(
        None,
        description="Relative shadow length (90 / altitude). None when below horizon."
    )


class SunPathSample(SunPositionResponse):
    hour: float = Field(..., ge=0, le=24, description="Local time in hours (0.5h steps)")


class SunPathResponse(BaseModel):
    date: str = Field(..., description="Local date (YYYY-MM-DD)")
    samples: list[SunPathSample] = Field(
        ..., description="25 samples from 6:00-18:00 at 0.5h intervals"
    )


class ShadowImpactResponse(BaseModel):
    """Estimated rooftop shadow coverage for one selected building."""

    structure_id: int = Field(..., description="City of Melbourne structure_id")
    date: str = Field(..., description="Local simulation date (YYYY-MM-DD)")
    hour: float = Field(..., ge=0, le=24, description="Local simulation hour")
    shadow_coverage_pct: float = Field(
        ..., ge=0, le=100, description="Estimated selected rooftop coverage shaded by nearby buildings"
    )
    shadowed_samples: int = Field(..., ge=0, description="Sample points inside the rooftop that were shaded")
    total_samples: int = Field(..., ge=0, description="Sample points used inside the selected rooftop footprint")
    shadow_caster_count: int = Field(..., ge=0, description="Nearby buildings casting shadows onto the selected rooftop")
    usable_roof_area_m2: float | None = Field(None, ge=0, description="Usable roof area used for unobstructed area estimate")
    unobstructed_usable_area_m2: float | None = Field(None, ge=0, description="Usable roof area remaining after estimated shadow coverage")
    overlay_geojson: dict[str, Any] = Field(..., description="GeoJSON rooftop cells split into shaded and unobstructed areas")
    impact: Literal["Low", "Moderate", "High"] = Field(..., description="Impact level derived from coverage percentage")
    approximate: bool = Field(True, description="True because footprint geometry is used as a rooftop proxy")

# --- /precincts (Epic 5) -----------------------------------------------------


class PrecinctSummary(BaseModel):
    precinct_id: int
    name: str
    postcode: str | None = None
    total_kwh_annual: float = Field(..., ge=0)
    total_usable_area_m2: float = Field(..., ge=0)
    installed_capacity_kw: float = Field(..., ge=0)
    potential_capacity_kw: float = Field(..., ge=0)
    adoption_gap_kw: float = Field(..., ge=0)
    building_count: int = Field(..., ge=0)
    rank: int | None = Field(None, description="Rank by the current sort key (1 = highest), only present in list responses")


class PrecinctDetail(PrecinctSummary):
    geo_boundary: dict[str, Any] | None = Field(
        None, description="GeoJSON Polygon/MultiPolygon"
    )


class PrecinctListResponse(BaseModel):
    sort: Literal["kwh", "area", "buildings", "gap"]
    precincts: list[PrecinctSummary]

class PshMonthlyResponse(BaseModel):
    """Monthly Peak Sun Hours constants (NASA POWER x BOM calibrated)."""

    location: str = Field(..., description="Location name, e.g. 'Melbourne'")
    psh_monthly: list[float] = Field(
        ..., min_length=12, max_length=12,
        description="Index 0=Jan to 11=Dec, unit: kWh/m²/day"
    )
    psh_annual_avg: float = Field(
        ..., ge=0, description="Annual average PSH (BOM station 086338, ~4.1)"
    )
