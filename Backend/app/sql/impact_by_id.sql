-- Fields needed for /buildings/{id}/impact.
-- Uses buildings.id (surrogate PK) → solar_api_cache via structure_id.
SELECT
    sac.structure_id,
    sac.max_panels,
    sac.panel_capacity_watts,
    sac.panel_lifetime_years,
    sac.carbon_offset_kg_per_mwh,
    sac.max_panels_kwh_annual
FROM solar_api_cache sac
JOIN buildings b ON b.structure_id = sac.structure_id
WHERE b.id = %(id)s;
