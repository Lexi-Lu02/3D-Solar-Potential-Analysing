"""
Trusted context payload from the frontend.

The frontend sends pre-computed / pre-fetched data (selected building details,
financial estimates the user is currently looking at, custom assumptions) in
a separate `context` field on `/ai/chat` and `/ai/report`. This data is
injected into the SYSTEM prompt as a "pre-computed context" block, so the
model treats the numbers as authoritative and does not waste tool calls
re-verifying them.

Important security property: the schema below is fully typed (no free-form
text fields except short, length-bounded strings like address). Anything the
user types still goes through the user-message scrubber. Only the structured
context goes through this trusted path.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BuildingContext(BaseModel):
    """Snapshot of the building the user is currently looking at on the frontend."""

    id: int = Field(..., ge=1, description="buildings.id (surrogate PK)")
    structure_id: int | None = Field(None, ge=1)
    address: str | None = Field(None, max_length=300)

    # Solar / roof
    solar_score: float | None = Field(None, ge=0, le=5)
    dominant_rating: str | None = Field(None, max_length=40)
    usable_roof_area_m2: float | None = Field(None, ge=0)
    total_roof_area_m2: float | None = Field(None, ge=0)
    max_panels: int | None = Field(None, ge=0)
    system_size_kw: float | None = Field(None, ge=0)

    # Yield
    annual_kwh: float | None = Field(None, ge=0)

    # Financial (already computed on the frontend or via /buildings/{id}/impact)
    install_cost_aud: float | None = Field(None, ge=0)
    annual_savings_aud: float | None = Field(None, ge=0)
    payback_years: float | None = Field(None, ge=0)
    lifetime_savings_aud: float | None = Field(None, ge=0)

    # Environmental
    co2_offset_kg_yr: float | None = Field(None, ge=0)
    equivalent_trees: float | None = Field(None, ge=0)


class PrecinctContext(BaseModel):
    """Snapshot of the precinct the user is currently looking at."""

    precinct_id: int = Field(..., ge=1)
    name: str | None = Field(None, max_length=100)
    postcode: str | None = Field(None, max_length=10)
    total_kwh_annual: float | None = Field(None, ge=0)
    total_usable_area_m2: float | None = Field(None, ge=0)
    installed_capacity_kw: float | None = Field(None, ge=0)
    potential_capacity_kw: float | None = Field(None, ge=0)
    adoption_gap_kw: float | None = Field(None, ge=0)
    building_count: int | None = Field(None, ge=0)
    rank: int | None = Field(None, ge=1)


class Assumptions(BaseModel):
    """User- or app-controlled assumptions baked into the displayed numbers."""

    electricity_tariff_aud_per_kwh: float | None = Field(None, ge=0, le=10)
    self_consumption_pct: float | None = Field(None, ge=0, le=100)
    panel_efficiency: float | None = Field(None, gt=0, le=1)
    performance_ratio: float | None = Field(None, gt=0, le=1)
    season: Literal["annual", "summer", "autumn", "winter", "spring"] | None = None


class ContextPayload(BaseModel):
    """Wrapper for everything the frontend wants the model to trust."""

    selected_building: BuildingContext | None = None
    selected_precinct: PrecinctContext | None = None
    assumptions: Assumptions | None = None


# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------


# Per-field rendering: (key, label, formatter). Numeric values get thousands
# separators; bare strings pass through. None values are skipped.
def _fmt_int(v: Any) -> str: return f"{int(v):,}"
def _fmt_float(v: Any, digits: int = 1) -> str: return f"{float(v):,.{digits}f}"
def _fmt_pct(v: Any) -> str: return f"{float(v):.0f}%"


_BUILDING_FIELDS: list[tuple[str, str, Any]] = [
    ("id",                    "id",                       _fmt_int),
    ("structure_id",          "structure_id",             _fmt_int),
    ("address",               "address",                  str),
    ("solar_score",           "solar_score (1-5)",        lambda v: _fmt_float(v, 2)),
    ("dominant_rating",       "dominant_rating",          str),
    ("usable_roof_area_m2",   "usable_roof_area_m2",      lambda v: _fmt_float(v, 1)),
    ("total_roof_area_m2",    "total_roof_area_m2",       lambda v: _fmt_float(v, 1)),
    ("max_panels",            "max_panels",               _fmt_int),
    ("system_size_kw",        "system_size_kw",           lambda v: _fmt_float(v, 2)),
    ("annual_kwh",            "annual_kwh",               _fmt_int),
    ("install_cost_aud",      "install_cost_aud",         _fmt_int),
    ("annual_savings_aud",    "annual_savings_aud",       _fmt_int),
    ("payback_years",         "payback_years",            lambda v: _fmt_float(v, 1)),
    ("lifetime_savings_aud",  "lifetime_savings_aud",     _fmt_int),
    ("co2_offset_kg_yr",      "co2_offset_kg_yr",         _fmt_int),
    ("equivalent_trees",      "equivalent_trees",         _fmt_int),
]


_PRECINCT_FIELDS: list[tuple[str, str, Any]] = [
    ("precinct_id",            "precinct_id",            _fmt_int),
    ("name",                   "name",                   str),
    ("postcode",               "postcode",               str),
    ("rank",                   "rank",                   _fmt_int),
    ("building_count",         "building_count",         _fmt_int),
    ("total_kwh_annual",       "total_kwh_annual",       _fmt_int),
    ("total_usable_area_m2",   "total_usable_area_m2",   _fmt_int),
    ("installed_capacity_kw",  "installed_capacity_kw",  lambda v: _fmt_float(v, 1)),
    ("potential_capacity_kw",  "potential_capacity_kw",  lambda v: _fmt_float(v, 1)),
    ("adoption_gap_kw",        "adoption_gap_kw",        lambda v: _fmt_float(v, 1)),
]


_ASSUMPTION_FIELDS: list[tuple[str, str, Any]] = [
    ("season",                          "season",                          str),
    ("electricity_tariff_aud_per_kwh",  "electricity_tariff_aud_per_kwh",  lambda v: _fmt_float(v, 3)),
    ("self_consumption_pct",            "self_consumption_pct",            _fmt_pct),
    ("panel_efficiency",                "panel_efficiency",                lambda v: _fmt_float(v, 3)),
    ("performance_ratio",               "performance_ratio",               lambda v: _fmt_float(v, 3)),
]


def _render_section(
    title: str,
    obj: BaseModel | None,
    fields: list[tuple[str, str, Any]],
) -> str | None:
    if obj is None:
        return None
    data = obj.model_dump()
    lines = [f"## {title}"]
    any_value = False
    for key, label, fmt in fields:
        v = data.get(key)
        if v is None:
            continue
        try:
            rendered = fmt(v)
        except Exception:
            rendered = str(v)
        lines.append(f"- {label}: {rendered}")
        any_value = True
    return "\n".join(lines) if any_value else None


def format_context(ctx: ContextPayload | None) -> str:
    """Render the trusted context as a Markdown block to append to the system prompt.

    Returns an empty string when there's nothing to render, so the caller can
    safely concatenate without checking.
    """
    if ctx is None:
        return ""

    sections = [
        _render_section("Selected building", ctx.selected_building, _BUILDING_FIELDS),
        _render_section("Selected precinct", ctx.selected_precinct, _PRECINCT_FIELDS),
        _render_section("Assumptions used", ctx.assumptions, _ASSUMPTION_FIELDS),
    ]
    body = "\n\n".join(s for s in sections if s)
    if not body:
        return ""

    return (
        "\n\n---\n\n"
        "# Currently selected building (trusted pre-computed data)\n"
        "The user has already selected this building on the map. THIS IS the\n"
        "building they are asking about. Do NOT ask the user to identify a\n"
        "building — the data below is already for their selected building.\n"
        "Cite these numbers directly without calling tools to re-look them up.\n"
        "Only use tools if the user asks about something NOT listed here\n"
        '(e.g. comparing buildings, suburb-wide stats, historical data).\n\n'
        f"{body}"
    )
