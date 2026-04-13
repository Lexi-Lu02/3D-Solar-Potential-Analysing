-- Fetch a single building by primary key, LEFT JOINed with its rooftop_solar
-- aggregate (if any). Used by GET /api/v1/buildings/{id}.
--
-- Parameter:
--   %(structure_id)s :: bigint
--
-- Returns at most one row. The rooftop_solar columns are NULL when the
-- building has no matching solar survey data (~5% of buildings).
SELECT
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
    -- address is populated by scripts/reverse_geocode_addresses.py (Phase D).
    -- NULL until the batch script has run and the column has been added via
    -- ALTER TABLE buildings ADD COLUMN IF NOT EXISTS address TEXT;
    b.address,
    s.total_roof_area,
    s.usable_roof_area,
    s.dominant_rating,
    s.solar_score_avg,
    s.roof_patch_count,
    s.excellent_area,
    s.usable_ratio
FROM buildings b
LEFT JOIN rooftop_solar s ON s.structure_id = b.structure_id
WHERE b.structure_id = %(structure_id)s;
