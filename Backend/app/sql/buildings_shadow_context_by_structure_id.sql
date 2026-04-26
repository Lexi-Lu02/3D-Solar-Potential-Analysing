WITH target AS (
    SELECT
        structure_id,
        lat,
        lng
    FROM buildings
    WHERE structure_id = %(structure_id)s
)
SELECT
    b.structure_id,
    b.lat,
    b.lng,
    b.building_height,
    b.base_height,
    b.max_elevation,
    b.min_elevation,
    b.geo_shape,
    s.usable_roof_area,
    (b.structure_id = %(structure_id)s) AS is_target
FROM buildings b
JOIN target t ON
    b.lat BETWEEN t.lat - %(lat_delta)s AND t.lat + %(lat_delta)s
    AND b.lng BETWEEN t.lng - %(lng_delta)s AND t.lng + %(lng_delta)s
LEFT JOIN rooftop_solar s ON s.structure_id = b.structure_id;
