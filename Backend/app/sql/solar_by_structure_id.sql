-- Fetch the solar API cache record by City of Melbourne structure_id.
-- Used by GET /api/v1/buildings/structure/{structure_id}/solar.
--
-- Parameter:
--   %(structure_id)s :: integer
--
-- Returns at most one row. Returns no rows if the structure has no entry in
-- solar_api_cache (the router converts that to a 404).
SELECT
    structure_id,
    address,
    max_panels,
    max_array_area_m2,
    min_panels_kwh_annual,
    max_panels_kwh_annual,
    max_sunshine_hours_per_year,
    carbon_offset_kg_per_mwh,
    whole_roof_area_m2,
    roof_segment_stats,
    solar_panel_configs,
    panel_capacity_watts
FROM solar_api_cache
WHERE structure_id = %(structure_id)s;
