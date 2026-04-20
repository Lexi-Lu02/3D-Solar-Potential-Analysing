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


# --- /buildings/{id}/yield ---------------------------------------------------


class YieldMonthlyItem(BaseModel):
    month: str = Field(..., description="月份缩写，例如 'Jan'")
    days: int = Field(..., ge=28, le=31, description="该月天数")
    psh: float = Field(..., ge=0, description="该月日均峰值日照时数（kWh/m²/day），NASA POWER 来源")
    kwh: int = Field(..., ge=0, description="该月估算发电量（kWh），已四舍五入为整数")


class YieldAssumptions(BaseModel):
    """
    用于计算本次 kWh 估算所使用的参数，方便前端展示"计算依据"或做灵敏度分析。
    """
    panel_efficiency: float = Field(
        ..., description="光伏板转换效率，当前固定为 0.20（20%）"
    )
    performance_ratio: float = Field(
        ..., description="系统性能比（逆变器损耗等），当前固定为 0.75"
    )
    peak_sun_hours_annual: float = Field(
        ..., description="BOM 校准后年均峰值日照时数（4.1 PSH/day）"
    )
    usable_roof_area_m2: float = Field(
        ..., ge=0, description="参与计算的可用屋顶面积（m²），来自 rooftop_solar 调研"
    )


class YieldResponse(BaseModel):
    structure_id: int = Field(..., description="City of Melbourne structure_id")
    has_data: bool = Field(
        ..., description="是否有光伏调研数据。False 时 kwh_annual=0，kwh_monthly=[]"
    )
    kwh_annual: int = Field(
        ..., ge=0,
        description="年度估算发电量（kWh）= sum(kwh_monthly)，保证与月度加总一致"
    )
    kwh_monthly: list[YieldMonthlyItem] = Field(
        ..., description="12 个月的发电量明细（has_data=False 时为空列表）"
    )
    assumptions: YieldAssumptions = Field(
        ..., description="本次计算所用的参数，供前端透明展示"
    )
