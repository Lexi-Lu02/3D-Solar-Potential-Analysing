-- 单个 precinct 详情，boundary 转 GeoJSON。
SELECT
    p.precinct_id,
    p.name,
    p.postcode,
    p.total_kwh_annual,
    p.total_usable_area_m2,
    p.installed_capacity_kw,
    p.potential_capacity_kw,
    p.adoption_gap_kw,
    ST_AsGeoJSON(p.geo_boundary) AS geo_boundary,
    COALESCE(bc.building_count, 0) AS building_count
FROM precincts p
LEFT JOIN (
    SELECT precinct_id, COUNT(*)::bigint AS building_count
    FROM buildings
    WHERE precinct_id = %(precinct_id)s
    GROUP BY precinct_id
) bc ON bc.precinct_id = p.precinct_id
WHERE p.precinct_id = %(precinct_id)s;
