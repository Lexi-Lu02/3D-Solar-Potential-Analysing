-- Return the address for a building by structure_id.
-- Falls back gracefully: prefers solar_api_cache.address, then buildings.address.
-- Used by GET /api/v1/buildings/by-structure/{structure_id}/address.
--
-- Parameter:
--   %(structure_id)s :: integer
--
-- Returns at most one row. Returns no rows if structure_id does not exist.
SELECT
    b.structure_id,
    COALESCE(sac.address, b.address) AS address
FROM buildings b
LEFT JOIN solar_api_cache sac ON sac.structure_id = b.structure_id
WHERE b.structure_id = %(structure_id)s
LIMIT 1;