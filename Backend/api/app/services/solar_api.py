import httpx
from app.config import get_settings
import os
os.environ["NO_PROXY"] = "solar.googleapis.com"
os.environ["no_proxy"] = "solar.googleapis.com"
SOLAR_BASE = "https://solar.googleapis.com/v1/buildingInsights:findClosest"


async def fetch_solar_from_google(lat: float, lng: float) -> dict:
    """
    Call the Google Solar API with the given coordinates and return
    a flat dict that maps directly to the solar_api_cache table columns.
    """
    settings = get_settings()
    params = {
        "location.latitude":  lat,
        "location.longitude": lng,
        "requiredQuality":    "LOW",
        "key":                settings.solar_api_key,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(SOLAR_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    si = data.get("solarPotential", {})

    configs = si.get("solarPanelConfigs", [{}])
    min_config = configs[0]
    max_config = configs[-1]

    return {
        "api_building_name":           data.get("name", ""),
        "center_lat":                  data["center"]["latitude"],
        "center_lng":                  data["center"]["longitude"],
        "postal_code":                 data.get("postalCode", ""),
        "administrative_area":         data.get("administrativeArea", ""),
        "region_code":                 data.get("regionCode", ""),
        "imagery_quality":             data.get("imageryQuality", ""),
        "imagery_date":                _parse_date(data.get("imageryDate")),
        "imagery_processed_date":      _parse_date(data.get("imageryProcessedDate")),
        "max_panels":                  si.get("maxArrayPanelsCount"),
        "max_array_area_m2":           si.get("maxArrayAreaMeters2"),
        "max_sunshine_hours_per_year": si.get("maxSunshineHoursPerYear"),
        "carbon_offset_kg_per_mwh":    si.get("carbonOffsetFactorKgPerMwh"),
        "panel_capacity_watts":        si.get("panelCapacityWatts"),
        "panel_height_m":              si.get("panelHeightMeters"),
        "panel_width_m":               si.get("panelWidthMeters"),
        "panel_lifetime_years":        si.get("panelLifetimeYears"),
        "whole_roof_area_m2":          si.get("wholeRoofStats", {}).get("areaMeters2"),
        "whole_roof_ground_area_m2":   si.get("wholeRoofStats", {}).get("groundAreaMeters2"),
        # List of sunshine quantiles across the whole roof surface
        "whole_roof_sunshine_quantiles": si.get("wholeRoofStats", {}).get("sunshineQuantiles"),
        # Annual DC energy yield for min and max panel configurations
        "min_panels_kwh_annual":       min_config.get("yearlyEnergyDcKwh"),
        "max_panels_kwh_annual":       max_config.get("yearlyEnergyDcKwh"),
        # Full JSON blobs stored as JSONB in Postgres
        "roof_segment_stats":          si.get("roofSegmentStats"),
        "solar_panel_configs":         si.get("solarPanelConfigs"),
        "address": data.get("postalAddress", {}).get("addressLines", [""])[0],
    }


def _parse_date(d: dict | None) -> str | None:
    """Convert a Google date object {year, month, day} to an ISO date string."""
    if not d:
        return None
    return f"{d['year']}-{d['month']:02d}-{d['day']:02d}"