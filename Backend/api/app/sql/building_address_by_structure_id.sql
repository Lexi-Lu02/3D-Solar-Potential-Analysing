-- Return the address for a building by structure_id from solar_api_cache.
-- Used by GET /api/v1/buildings/by-structure/{structure_id}/address.
--
-- Parameter:
--   %(structure_id)s :: integer
--
-- Returns at most one row. Returns no rows if structure_id has no cache entry.
SELECT
    b.structure_id,
    sac.address
FROM buildings b
LEFT JOIN solar_api_cache sac ON sac.structure_id = b.structure_id
WHERE b.structure_id = %(structure_id)s
LIMIT 1;