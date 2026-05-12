-- Fetch a single building by surrogate primary key (buildings.id),
-- LEFT JOINed with solar_api_cache (address), rooftop_solar (legacy solar
-- survey data), and solar_score (LightGBM model prediction, see SolarScoreModel/).
-- Used by GET /api/v1/buildings/{id}.
--
-- Parameter:
--   %(id)s :: integer  (buildings.id surrogate PK)
--
-- Returns at most one row. Joined columns are NULL when no matching record.
-- Service layer prefers solar_score.predicted_score_0_100 over the legacy
-- (solar_score_avg - 1) / 4 * 100 mapping.
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
    -- address lives in solar_api_cache (populated by reverse_geocode_addresses.py)
    sac.address,
    s.total_roof_area,
    s.usable_roof_area,
    s.dominant_rating,
    s.solar_score_avg,
    s.roof_patch_count,
    s.excellent_area,
    s.usable_ratio,
    -- LightGBM model prediction (see SolarScoreModel/REPORT.md)
    ss.predicted_score_0_100 AS model_solar_score,
    ss.predicted_score_1_5   AS model_solar_score_raw,
    ss.model_version         AS model_solar_score_version
FROM buildings b
LEFT JOIN solar_api_cache sac ON sac.structure_id = b.structure_id
LEFT JOIN rooftop_solar s     ON s.structure_id   = b.structure_id
LEFT JOIN solar_score ss      ON ss.structure_id  = b.structure_id
WHERE b.id = %(id)s;
