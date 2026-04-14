-- Fetch the full solar API cache record for a building identified by buildings.id.
-- Used by GET /api/v1/buildings/{id}/solar.
--
-- Parameter:
--   %(id)s :: integer  (buildings.id surrogate PK)
--
-- Returns at most one row. Returns no rows if the building has no entry in
-- solar_api_cache (the router converts that to a 404).
SELECT sac.*
FROM solar_api_cache sac
JOIN buildings b ON b.structure_id = sac.structure_id
WHERE b.id = %(id)s;
