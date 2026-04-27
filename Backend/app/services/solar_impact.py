"""Financial + environmental impact for one building."""

from __future__ import annotations

import math
from typing import Any, Literal

from psycopg import Connection
from psycopg.rows import dict_row

from ..constants.melbourne_psh import MONTHLY_PSH
from ..models.schemas import (
    EnvironmentalImpact,
    FinancialImpact,
    ImpactAssumptions,
    ImpactResponse,
)
from ..sql import load

Season = Literal["annual", "summer", "autumn", "winter", "spring"]

# Tweak these to update the dollar / CO2 numbers everywhere.
ELECTRICITY_TARIFF_AUD_PER_KWH = 0.30      # VIC 2025, self-consumption only
COST_PER_KW_INSTALLED_AUD = 1100           # Solar Choice 2025 median, post-STC
FALLBACK_GRID_KG_CO2_PER_KWH = 0.79        # DCCEEW 2024 VIC fallback
KG_CO2_ABSORBED_PER_TREE_YEAR = 22         # EPA Australia
KG_CO2_PER_LITRE_PETROL = 2.31             # NGA Factors 2024
KG_CO2_PER_CAR_YEAR = 4500                 # AU avg passenger car
DEFAULT_PANEL_WATTS = 410
DEFAULT_PANEL_LIFETIME_YEARS = 25

_SEASON_MONTHS: dict[Season, list[int]] = {
    "summer": [12, 1, 2],
    "autumn": [3, 4, 5],
    "winter": [6, 7, 8],
    "spring": [9, 10, 11],
    "annual": list(range(1, 13)),
}


class BuildingNotFoundForImpact(Exception):
    def __init__(self, id: int):
        super().__init__(f"building {id} not found")
        self.id = id


def fetch_impact(conn: Connection, id: int, season: Season) -> ImpactResponse:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(load("impact_by_id"), {"id": id})
        row = cur.fetchone()
    if row is None:
        raise BuildingNotFoundForImpact(id)
    return compute_impact(row, season)


def compute_impact(row: dict[str, Any], season: Season = "annual") -> ImpactResponse:
    """Pure function. Every numeric output is None if the input is missing."""
    max_panels = _int_or_none(row.get("max_panels"))
    base_kwh = _float_or_none(row.get("max_panels_kwh_annual"))
    watts_per_panel = _float_or_none(row.get("panel_capacity_watts")) or DEFAULT_PANEL_WATTS
    panel_lifetime = _int_or_none(row.get("panel_lifetime_years")) or DEFAULT_PANEL_LIFETIME_YEARS
    co2_factor_mwh = _float_or_none(row.get("carbon_offset_kg_per_mwh"))

    kwh_seasonal = (
        round(base_kwh * _season_factor(season), 1) if base_kwh else None
    )
    system_size_kw = (
        round(max_panels * watts_per_panel / 1000, 1) if max_panels else None
    )

    # Financial
    installation_cost = (
        round(system_size_kw * COST_PER_KW_INSTALLED_AUD)
        if system_size_kw else None
    )
    annual_savings = (
        round(kwh_seasonal * ELECTRICITY_TARIFF_AUD_PER_KWH)
        if kwh_seasonal else None
    )
    payback_years = (
        round(installation_cost / annual_savings, 1)
        if installation_cost and annual_savings else None
    )
    lifetime_net_savings = (
        round(panel_lifetime * annual_savings - installation_cost)
        if installation_cost is not None and annual_savings is not None else None
    )

    # Environmental
    if co2_factor_mwh is not None:
        co2_kg_per_kwh = co2_factor_mwh / 1000
        co2_source = "google_api"
    else:
        co2_kg_per_kwh = FALLBACK_GRID_KG_CO2_PER_KWH
        co2_source = "dcceew_2024_fallback"

    annual_co2_kg = (
        round(kwh_seasonal * co2_kg_per_kwh) if kwh_seasonal else None
    )
    equivalent_trees = (
        round(annual_co2_kg / KG_CO2_ABSORBED_PER_TREE_YEAR)
        if annual_co2_kg else None
    )
    equivalent_petrol_l = (
        round(annual_co2_kg / KG_CO2_PER_LITRE_PETROL)
        if annual_co2_kg else None
    )
    equivalent_cars = (
        round(annual_co2_kg / KG_CO2_PER_CAR_YEAR, 1)
        if annual_co2_kg else None
    )

    return ImpactResponse(
        structure_id=int(row["structure_id"]) if row.get("structure_id") is not None else 0,
        season=season,
        kwh_annual_seasonal=kwh_seasonal,
        kwh_annual_base=base_kwh,
        system_size_kw=system_size_kw,
        financial=FinancialImpact(
            installation_cost_aud=installation_cost,
            annual_savings_aud=annual_savings,
            payback_years=payback_years,
            lifetime_years=panel_lifetime,
            lifetime_net_savings_aud=lifetime_net_savings,
        ),
        environmental=EnvironmentalImpact(
            annual_co2_reduction_kg=annual_co2_kg,
            co2_kg_per_kwh_used=round(co2_kg_per_kwh, 4),
            co2_factor_source=co2_source,
            equivalent_trees=equivalent_trees,
            equivalent_petrol_litres=equivalent_petrol_l,
            equivalent_cars=equivalent_cars,
        ),
        assumptions=ImpactAssumptions(
            electricity_tariff_aud_per_kwh=ELECTRICITY_TARIFF_AUD_PER_KWH,
            cost_per_kw_installed_aud=COST_PER_KW_INSTALLED_AUD,
            self_consumption_pct=100,
            feed_in_tariff_included=False,
        ),
    )


# --- helpers ----------------------------------------------------------------


def _season_factor(season: Season) -> float:
    """Annualised multiplier: PSH share of those months × (12 / months)."""
    months = _SEASON_MONTHS.get(season, _SEASON_MONTHS["annual"])
    season_psh = sum(MONTHLY_PSH[m - 1] for m in months)
    annual_psh = sum(MONTHLY_PSH)
    return (season_psh / annual_psh) * (12 / len(months))


def _float_or_none(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _int_or_none(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
