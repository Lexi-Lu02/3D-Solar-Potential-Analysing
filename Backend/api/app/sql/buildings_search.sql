-- Search buildings by address (case-insensitive partial match).
-- Used by GET /api/v1/buildings/search?q=.
--
-- Parameter:
--   %(q)s :: text  — already wrapped with % wildcards by the service layer,
--                    e.g. '%Collins%' for q='Collins'
--
-- Only returns buildings that have an address in solar_api_cache.
-- Results are ordered alphabetically and capped at 20 rows.
SELECT
    b.id,
    b.structure_id,
    b.lat,
    b.lng,
    sac.address
FROM solar_api_cache sac
JOIN buildings b ON b.structure_id = sac.structure_id
WHERE sac.address ILIKE %(q)s
ORDER BY sac.address
LIMIT 20;
