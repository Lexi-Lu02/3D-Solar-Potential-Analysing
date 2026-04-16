-- Fetch the solar API cache record by City of Melbourne structure_id.
-- Used by GET /api/v1/buildings/structure/{structure_id}/solar.
--
-- Parameter:
--   %(structure_id)s :: integer
--
-- Returns at most one row. Returns no rows if the structure has no entry in
-- solar_api_cache (the router converts that to a 404).
SELECT *
FROM solar_api_cache
WHERE structure_id = %(structure_id)s;
