-- Fetch the solar area data needed to compute kWh yield for one building.
-- Used by GET /api/v1/buildings/{id}/yield.
--
-- Parameter:
--   %(structure_id)s :: bigint
--
-- Returns at most one row. s.usable_roof_area is NULL when the building has
-- no matching rooftop_solar survey record (~5% of buildings); the service
-- layer treats that as has_data=false and returns zero kWh.
SELECT
    b.structure_id,
    s.usable_roof_area
FROM buildings b
LEFT JOIN rooftop_solar s ON s.structure_id = b.structure_id
WHERE b.structure_id = %(structure_id)s;
