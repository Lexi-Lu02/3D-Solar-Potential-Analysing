-- Fetch the solar API cache record by City of Melbourne structure_id.
-- Also JOINs buildings to provide address even when solar_api_cache.address
-- is unpopulated (buildings.address is filled by reverse_geocode_addresses.py).
-- Used by GET /api/v1/buildings/structure/{structure_id}/solar.
--
-- Parameter:
--   %(structure_id)s :: integer
--
-- Returns at most one row. Returns no rows if the structure has no entry in
-- solar_api_cache (the router converts that to a 404).
SELECT
    sac.structure_id,
    COALESCE(sac.address, b.address) AS address,
    sac.max_panels,
    sac.max_array_area_m2,
    sac.max_panels_kwh_annual,
    sac.max_sunshine_hours_per_year,
    sac.carbon_offset_kg_per_mwh,
    sac.whole_roof_area_m2,
    sac.roof_segment_stats,
    sac.solar_panel_configs
FROM solar_api_cache sac
LEFT JOIN buildings b ON b.structure_id = sac.structure_id
WHERE sac.structure_id = %(structure_id)s;
