SELECT
    COUNT(DISTINCT b.structure_id)                                        AS total_buildings,
    COALESCE(SUM(s.usable_roof_area), 0)                                  AS usable_area_m2,
    COALESCE(SUM(s.usable_roof_area * 0.20 * 0.75 * 1496.5), 0)          AS kwh_annual,
    COUNT(DISTINCT CASE WHEN s.solar_score_avg >= 3.4
          THEN b.structure_id END)                                         AS high_potential_count
FROM buildings b
LEFT JOIN rooftop_solar s ON s.structure_id = b.structure_id;
