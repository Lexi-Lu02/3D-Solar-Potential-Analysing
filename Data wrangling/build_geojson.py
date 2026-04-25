"""
Build combined-buildings.geojson
=================================
Joins buildings.csv + rooftop_solar.csv and writes a GeoJSON
FeatureCollection to ../Backend/combined-buildings.geojson.

Run from the "Data wrangling" folder:
    python build_geojson.py

Area methodology
----------------
- footprint_area      : actual 2D roof footprint in m², computed from the
                        geo_shape polygon via the spherical shoelace formula.
                        Available for all 40,951 buildings.
- usable_roof_area    : footprint_area × usable_ratio (from the solar survey).
                        Represents the realistic usable solar area tied to the
                        building's true footprint size.  0 for buildings with
                        no solar data.
- kwh_annual          : estimated from usable_roof_area using the standard
                        Melbourne CBD formula (4.1 PSH, 20% efficiency, 0.75 PR).
"""

import json
import math
import os
import pandas as pd

BUILDINGS_CSV    = 'buildings.csv'
SOLAR_CSV        = 'rooftop_solar.csv'
SOLAR_SCORE_CSV  = 'solar_score.csv'   # exported from solar_score table: structure_id, composite_score
OUTPUT_GEOJSON   = '../Backend/combined-buildings.geojson'

# kWh formula constants (Melbourne CBD, BOM validated)
PANEL_EFFICIENCY  = 0.20
PERFORMANCE_RATIO = 0.75
PEAK_SUN_HOURS    = 4.1
DAYS_PER_YEAR     = 365


def safe_float(val, default=0.0):
    try:
        v = float(val)
        return default if math.isnan(v) else v
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0):
    try:
        v = float(val)
        return default if math.isnan(v) else int(v)
    except (TypeError, ValueError):
        return default


def polygon_area_m2(geojson_str):
    """
    Compute the 2D footprint area of a GeoJSON Polygon in square metres.

    Uses the spherical shoelace formula with a local equirectangular
    projection centred on the polygon centroid.  Accurate to ~0.1% for
    building-scale polygons anywhere in Melbourne.
    """
    try:
        geom   = json.loads(geojson_str)
        coords = geom['coordinates'][0]          # outer ring only
        lats   = [c[1] for c in coords]
        lat0   = sum(lats) / len(lats)           # centroid latitude

        # metres per degree at this latitude
        lat_scale = math.pi * 6_371_000 / 180
        lng_scale = lat_scale * math.cos(math.radians(lat0))

        # Shoelace formula on locally-projected coordinates
        area = 0.0
        n = len(coords)
        for i in range(n - 1):
            x1 = coords[i][0]     * lng_scale
            y1 = coords[i][1]     * lat_scale
            x2 = coords[i + 1][0] * lng_scale
            y2 = coords[i + 1][1] * lat_scale
            area += x1 * y2 - x2 * y1
        return round(abs(area) / 2, 1)
    except Exception:
        return 0.0


def main():
    print('Reading CSVs...')
    buildings = pd.read_csv(BUILDINGS_CSV)
    solar     = pd.read_csv(SOLAR_CSV)
    print(f'  buildings:     {len(buildings):,} rows')
    print(f'  rooftop_solar: {len(solar):,} rows')

    # Join rooftop_solar data onto buildings
    df = buildings.merge(solar, on='structure_id', how='left')

    # Solar score: prefer composite_score from solar_score table (0–100, computed by
    # solar score.py).  Fall back to rescaling solar_score_avg (1–5) from rooftop_solar
    # for any buildings not yet in the solar_score table.
    if os.path.isfile(SOLAR_SCORE_CSV):
        scores = pd.read_csv(SOLAR_SCORE_CSV)[['structure_id', 'composite_score']]
        print(f'  solar_score:   {len(scores):,} rows (from {SOLAR_SCORE_CSV})')
        df = df.merge(scores, on='structure_id', how='left')
        df['solar_score'] = df['composite_score'].apply(
            lambda x: round(safe_float(x)) if not math.isnan(safe_float(x, float('nan'))) else 0
        )
    else:
        print(f'  solar_score:   {SOLAR_SCORE_CSV} not found — falling back to solar_score_avg')
        df['solar_score'] = df['solar_score_avg'].apply(
            lambda x: round((safe_float(x) - 1) / 4 * 100)
                      if not math.isnan(safe_float(x, float('nan'))) else 0
        )

    print('Building GeoJSON features...')
    features = []
    skipped  = 0

    for _, row in df.iterrows():
        # Parse geometry
        try:
            geometry = json.loads(row['geo_shape'])
        except (TypeError, ValueError, KeyError):
            skipped += 1
            continue

        has_solar    = not math.isnan(safe_float(row.get('solar_score_avg'), float('nan')))
        usable_ratio = safe_float(row.get('usable_ratio')) if has_solar else 0.0

        # Actual building footprint area from the polygon
        footprint_area = polygon_area_m2(row['geo_shape'])

        # Usable solar area = real footprint × fraction that is Good/Excellent
        usable_roof_area = round(footprint_area * usable_ratio, 1)

        # kWh estimate based on usable_roof_area
        kwh_annual = round(
            usable_roof_area
            * PANEL_EFFICIENCY
            * PERFORMANCE_RATIO
            * PEAK_SUN_HOURS
            * DAYS_PER_YEAR
        )

        props = {
            # Identity
            'structure_id':  safe_int(row['structure_id']),
            'roof_type':     str(row.get('roof_type') or ''),
            'date_captured': str(row.get('date_captured') or ''),
            # Geometry / height (used for 3D extrusion)
            'building_height': safe_float(row.get('building_height')),
            'base_height':     safe_float(row.get('base_height')),
            'max_elevation':   safe_float(row.get('max_elevation')),
            'min_elevation':   safe_float(row.get('min_elevation')),
            # Location
            'lat': safe_float(row.get('lat')),
            'lng': safe_float(row.get('lng')),
            # Area — grounded in actual building footprint
            'footprint_area':    footprint_area,
            'usable_roof_area':  usable_roof_area,
            # Solar data
            'solar_score':      safe_int(row['solar_score']),
            'solar_score_avg':  safe_float(row.get('solar_score_avg')),
            'kwh_annual':       float(kwh_annual),
            'dominant_rating':  str(row.get('dominant_rating') or '') if has_solar else '',
            'usable_ratio':     usable_ratio,
            'roof_patch_count': safe_int(row.get('roof_patch_count')),
            'excellent_area':   safe_float(row.get('excellent_area')),
            'has_solar_data':   has_solar,
        }

        features.append({'type': 'Feature', 'geometry': geometry, 'properties': props})

    geojson = {'type': 'FeatureCollection', 'features': features}

    os.makedirs(os.path.dirname(OUTPUT_GEOJSON), exist_ok=True)
    print(f'Writing {OUTPUT_GEOJSON}...')
    with open(OUTPUT_GEOJSON, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, separators=(',', ':'))

    size_mb = os.path.getsize(OUTPUT_GEOJSON) / 1_000_000
    print(f'\nDone: {len(features):,} buildings written ({size_mb:.1f} MB), {skipped} skipped')


if __name__ == '__main__':
    main()
