import geopandas as gpd
import pandas as pd
from shapely import from_geojson
import warnings
warnings.filterwarnings('ignore')
 
 

SOLAR_SHP         = 'mga55_gda95_green_roof_solar.shp'
BUILDINGS_CSV     = '2023-building-footprints.csv'
OUTPUT_BUILDINGS  = 'buildings.csv'
OUTPUT_SOLAR      = 'rooftop_solar.csv'
 
 
# Step 1: Load raw data
print("[1] Loading raw data...")
solar         = gpd.read_file(SOLAR_SHP)
buildings_raw = pd.read_csv(BUILDINGS_CSV)
print(f"  Solar roof polygons:  {len(solar)} rows")
print(f"  Building footprints:  {len(buildings_raw)} rows")
 
 
# Step 2: Clean building footprints
print("[2] Cleaning building footprints...")
 
# Convert GeoJSON strings to geometry objects and reproject to EPSG:28355
# (must match the Solar shapefile coordinate system)
buildings_raw['geometry'] = buildings_raw['Geo Shape'].apply(from_geojson)
buildings_gdf = gpd.GeoDataFrame(
    buildings_raw, geometry='geometry', crs='EPSG:4326'
).to_crs('EPSG:28355')
 
# Extract latitude and longitude from 'Geo Point' column
buildings_raw[['lat', 'lng']] = (
    buildings_raw['Geo Point']
    .str.split(', ', expand=True)
    .astype(float)
)
 
# Format date: 20180528 -> 2018-05-28
buildings_raw['date_captured'] = pd.to_datetime(
    buildings_raw['date_captured'].astype(str), format='%Y%m%d'
)
 
# Keep only 'Structure' type (remove walls, fences, etc.)
buildings_clean = buildings_raw[
    buildings_raw['footprint_type'] == 'Structure'
].copy()
print(f"  Filtered buildings: {len(buildings_clean)} (original: {len(buildings_raw)})")
 
 
# Step 3: Clean solar shapefile
print("[3] Cleaning solar data...")
 
# Map RATING text to numeric score
rating_map = {
    'Excellent': 5,
    'Good':      4,
    'Moderate':  3,
    'Poor':      2,
    'Very Poor': 1,
}
solar['solar_score'] = solar['RATING'].map(rating_map)
 
# Remove tiny noise polygons (< 4 m2)
solar_clean = solar[solar['Shape_Area'] >= 4].copy()
print(f"  Filtered roof polygons: {len(solar_clean)} (original: {len(solar)})")
 
 
# Step 4: Spatial join - match each roof polygon to a building
print("[4] Running spatial join: roof polygons -> buildings...")
 
joined = gpd.sjoin(
    solar_clean,
    buildings_gdf[['structure_id', 'geometry']],
    how='left',
    predicate='intersects'
)
 
# A roof polygon may intersect multiple buildings - keep only the first match
joined = joined[~joined.index.duplicated(keep='first')]
 
matched_count = joined['structure_id'].notna().sum()
print(f"  Match rate: {matched_count / len(joined) * 100:.1f}%")
 
 
# Step 5: Aggregate solar data per building
print("[5] Aggregating solar data by building...")
 
matched = joined[joined['structure_id'].notna()].copy()
matched['structure_id'] = matched['structure_id'].astype(int)
 
solar_agg = matched.groupby('structure_id').agg(
    total_roof_area  = ('Shape_Area', 'sum'),
    usable_roof_area = ('Shape_Area', lambda x:
                        x[matched.loc[x.index, 'solar_score'] >= 4].sum()),
    dominant_rating  = ('RATING', lambda x: x.value_counts().index[0]),
    solar_score_avg  = ('solar_score', 'mean'),
    roof_patch_count = ('Shape_Area', 'count'),
    excellent_area   = ('Shape_Area', lambda x:
                        x[matched.loc[x.index, 'solar_score'] == 5].sum()),
).reset_index()
 
solar_agg['usable_ratio']     = (solar_agg['usable_roof_area'] / solar_agg['total_roof_area']).round(3)
solar_agg['solar_score_avg']  = solar_agg['solar_score_avg'].round(2)
solar_agg['total_roof_area']  = solar_agg['total_roof_area'].round(1)
solar_agg['usable_roof_area'] = solar_agg['usable_roof_area'].round(1)
solar_agg['excellent_area']   = solar_agg['excellent_area'].round(1)
 
print(f"  Buildings aggregated: {len(solar_agg)}")
 
 
# Step 6: Build buildings table
print("[6] Building the buildings table...")
 
buildings_table = buildings_clean[[
    'structure_id',
    'lat', 'lng',
    'roof_type',
    'footprint_type',
    'structure_extrusion',
    'footprint_extrusion',
    'structure_max_elevation',
    'structure_min_elevation',
    'date_captured',
    'Geo Shape',
]].copy()
 
buildings_table.rename(columns={
    'Geo Shape':               'geo_shape',
    'structure_extrusion':     'building_height',
    'footprint_extrusion':     'base_height',
    'structure_max_elevation': 'max_elevation',
    'structure_min_elevation': 'min_elevation',
}, inplace=True)
 
 
# Step 7: Deduplicate buildings
# One building can have multiple records (tower, podium, setbacks).
# Keep the row with the highest building_height per structure_id.
print("[7] Deduplicating buildings...")
 
buildings_table = (
    buildings_table
    .sort_values('building_height', ascending=False)
    .drop_duplicates(subset='structure_id', keep='first')
    .sort_values('structure_id')
    .reset_index(drop=True)
)
print(f"  After dedup: {len(buildings_table)} rows")
 
 
# Step 8: Filter rooftop_solar to valid structure_ids only
# Remove orphaned records to satisfy the foreign key constraint
print("[8] Filtering rooftop_solar to valid structure_ids...")
 
valid_ids = set(buildings_table['structure_id'])
solar_agg = solar_agg[solar_agg['structure_id'].isin(valid_ids)].reset_index(drop=True)
print(f"  After filter: {len(solar_agg)} rows")
 
 
# Step 9: Export to CSV
print("[9] Exporting CSV files...")
buildings_table.to_csv(OUTPUT_BUILDINGS, index=False)
solar_agg.to_csv(OUTPUT_SOLAR, index=False)
 
print(f"\nDone!")
print(f"  {OUTPUT_BUILDINGS}: {len(buildings_table)} rows, columns: {list(buildings_table.columns)}")
print(f"  {OUTPUT_SOLAR}: {len(solar_agg)} rows, columns: {list(solar_agg.columns)}")
print(f"\nImport into PostgreSQL (run in order):")
print(f"  \\copy buildings     FROM '{OUTPUT_BUILDINGS}' CSV HEADER")
print(f"  \\copy rooftop_solar FROM '{OUTPUT_SOLAR}' CSV HEADER")