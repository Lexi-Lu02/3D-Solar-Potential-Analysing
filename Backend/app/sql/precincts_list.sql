-- 列出所有 precinct，附带实时 building_count。
-- building_count 现算，避免改数据流水线。
SELECT
    p.precinct_id,
    p.name,
    p.postcode,
    p.total_kwh_annual,
    p.total_usable_area_m2,
    p.installed_capacity_kw,
    p.potential_capacity_kw,
    p.adoption_gap_kw,
    COALESCE(bc.building_count, 0) AS building_count
FROM precincts p
LEFT JOIN (
    SELECT precinct_id, COUNT(*)::bigint AS building_count
    FROM buildings
    WHERE precinct_id IS NOT NULL
    GROUP BY precinct_id
) bc ON bc.precinct_id = p.precinct_id;
