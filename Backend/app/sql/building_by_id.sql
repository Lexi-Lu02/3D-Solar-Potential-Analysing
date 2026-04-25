-- Fetch a single building by surrogate primary key (buildings.id),
-- LEFT JOINed with solar_api_cache (for address) and rooftop_solar (solar data).
-- Used by GET /api/v1/buildings/{id}.
--
-- Parameter:
--   %(id)s :: integer  (buildings.id surrogate PK)
--
-- Returns at most one row. solar_api_cache and rooftop_solar columns are NULL
-- when the building has no matching record (roughly 5 percent of buildings
-- have no solar data).
SELECT
    b.id,
    b.structure_id,
    b.lat,
    b.lng,
    b.roof_type,
    b.building_height,
    b.base_height,
    b.max_elevation,
    b.min_elevation,
    b.date_captured,
    b.geo_shape,
    -- address lives in solar_api_cache, populated by
    -- scripts/reverse_geocode_addresses.py (Phase D).
    sac.address,
    s.total_roof_area,
    s.usable_roof_area,
    s.dominant_rating,
    s.solar_score_avg,
    s.roof_patch_count,
    s.excellent_area,
    s.usable_ratio
FROM buildings b
LEFT JOIN solar_api_cache sac ON sac.structure_id = b.structure_id
LEFT JOIN rooftop_solar s    ON s.structure_id    = b.structure_id
WHERE b.id = %(id)s;
