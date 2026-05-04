-- Fetch the solar area data needed to compute kWh yield for one building.
-- Used by GET /api/v1/buildings/structure/{structure_id}/yield.
--
-- Parameter:
--   %(structure_id)s :: integer  (City of Melbourne structure_id)
--
-- Returns at most one row. s.usable_roof_area is NULL when the building has
-- no matching rooftop_solar survey record; the service layer treats that as
-- has_data=false and returns zero kWh.
-- solar_score_avg is the 1–5 average patch rating from the survey (NULL when no data).
SELECT
    b.structure_id,
    s.usable_roof_area,
    s.solar_score_avg
FROM buildings b
LEFT JOIN rooftop_solar s ON s.structure_id = b.structure_id
WHERE b.structure_id = %(structure_id)s;
