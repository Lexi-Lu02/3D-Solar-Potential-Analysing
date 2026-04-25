import geopandas as gpd
import pandas as pd
import psycopg2
import psycopg2.extras
from shapely.geometry import box
import os

DB_HOST     = "127.0.0.1"
DB_PORT     = 5433
DB_NAME     = "melbourne_solar"
DB_USER     = "teamuser"
DB_PASSWORD = "123456"

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Step 1: Get actual building extent from local CSV
buildings_df = pd.read_csv("buildings.csv")

min_lng = buildings_df["lng"].min()
max_lng = buildings_df["lng"].max()
min_lat = buildings_df["lat"].min()
max_lat = buildings_df["lat"].max()

print(f"Buildings extent: lng {min_lng:.4f}~{max_lng:.4f}, lat {min_lat:.4f}~{max_lat:.4f}")

# Add small buffer to avoid clipping edge buildings
buildings_box = box(min_lng - 0.001, min_lat - 0.001, max_lng + 0.001, max_lat + 0.001)

# Step 2: Load ABS shapefile and filter to Victoria
gdf = gpd.read_file("precincts_data/SAL_2021_AUST_GDA2020.shp")
vic = gdf[gdf["STE_CODE21"] == "2"]

# Step 3: Select suburbs that intersect with actual building extent
bbox_gdf = gpd.GeoDataFrame(geometry=[buildings_box], crs="EPSG:4326").to_crs(vic.crs)
cbd = vic[vic.geometry.intersects(bbox_gdf.geometry[0])].copy()

print(f"\nFound {len(cbd)} suburbs matching building extent:")
print(cbd["SAL_NAME21"].tolist())

# Step 4: Reproject to WGS84 and rename columns to match precincts table schema
cbd_wgs84 = cbd.to_crs(epsg=4326)
cbd_wgs84 = cbd_wgs84[["SAL_CODE21", "SAL_NAME21", "geometry"]].copy()
cbd_wgs84.columns = ["precinct_id", "name", "geometry"]
cbd_wgs84["total_kwh_annual"] = None
cbd_wgs84["total_usable_area_m2"] = None
cbd_wgs84["installed_capacity_kw"] = None

# Step 5: Read CER postcode capacity CSV and compute adoption_gap_kw
print("\n[5] Reading Postcode capacity.csv...")
cer = pd.read_csv("Postcode capacity.csv")
cer.columns = [c.strip() for c in cer.columns]
cer["Postcode"] = cer["Postcode"].astype(str).str.strip()

# Sum all capacity columns (kW) to get total installed_capacity_kw per postcode
capacity_cols = [c for c in cer.columns if c != "Postcode"]
cer["installed_capacity_kw"] = cer[capacity_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
cer_lookup = cer.set_index("Postcode")["installed_capacity_kw"].to_dict()

# Suburb -> postcode mapping for the 40 precincts
SUBURB_POSTCODE = {
    "Abbotsford":    "3067",
    "Albert Park":   "3206",
    "Ascot Vale":    "3032",
    "Brunswick":     "3056",
    "Brunswick East":"3057",
    "Brunswick West":"3055",
    "Carlton":       "3053",
    "Carlton North": "3054",
    "Clifton Hill":  "3068",
    "Collingwood":   "3066",
    "Cremorne":      "3121",
    "Docklands":     "3008",
    "East Melbourne":"3002",
    "Fitzroy":       "3065",
    "Fitzroy North": "3068",
    "Flemington":    "3031",
    "Footscray":     "3011",
    "Kensington":    "3031",
    "Maribyrnong":   "3032",
    "Melbourne":     "3000",
    "Middle Park":   "3206",
    "Newport":       "3015",
    "North Melbourne":"3051",
    "Northcote":     "3070",
    "Parkville":     "3052",
    "Port Melbourne":"3207",
    "Prahran":       "3181",
    "Princes Hill":  "3054",
    "Richmond":      "3121",
    "Seddon":        "3011",
    "South Melbourne":"3205",
    "South Wharf":   "3006",
    "South Yarra":   "3141",
    "Southbank":     "3006",
    "Spotswood":     "3015",
    "Travancore":    "3032",
    "West Melbourne":"3003",
    "Williamstown":  "3016",
    "Windsor":       "3181",
    "Yarraville":    "3013",
}

cbd_wgs84["name"] = cbd_wgs84["name"].str.replace(r"\s*\(Vic\.\)", "", regex=True).str.strip()
cbd_wgs84["postcode"] = cbd_wgs84["name"].map(SUBURB_POSTCODE)
cbd_wgs84["installed_capacity_kw"] = cbd_wgs84["postcode"].map(cer_lookup)

missing = cbd_wgs84[cbd_wgs84["installed_capacity_kw"].isna()]["name"].tolist()
if missing:
    print(f"  Warning: no CER data for: {missing}")
print(f"  Matched {cbd_wgs84['installed_capacity_kw'].notna().sum()} / {len(cbd_wgs84)} precincts")

# Step 6: Aggregate solar data from DB per precinct via spatial join
print("\n[6] Connecting to DB and aggregating solar data per precinct...")
conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                        user=DB_USER, password=DB_PASSWORD)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Pull buildings with their lat/lng and solar cache data
cur.execute("""
    SELECT
        b.structure_id,
        b.lat,
        b.lng,
        s.max_panels_kwh_annual,
        s.max_array_area_m2,
        s.max_panels,
        s.panel_capacity_watts
    FROM buildings b
    JOIN solar_api_cache s USING (structure_id)
    WHERE s.max_panels_kwh_annual IS NOT NULL
      AND s.max_array_area_m2     IS NOT NULL
      AND s.max_panels            IS NOT NULL
""")
rows = cur.fetchall()
cur.close()
conn.close()
print(f"  Fetched {len(rows)} buildings from DB")

# Convert to GeoDataFrame with point geometry
buildings_gdf = gpd.GeoDataFrame(
    rows,
    columns=["structure_id", "lat", "lng", "max_panels_kwh_annual",
             "max_array_area_m2", "max_panels", "panel_capacity_watts"],
    geometry=gpd.points_from_xy([r["lng"] for r in rows], [r["lat"] for r in rows]),
    crs="EPSG:4326"
)

# Spatial join: assign each building to a precinct
joined = gpd.sjoin(buildings_gdf, cbd_wgs84[["precinct_id", "name", "geometry"]],
                   how="inner", predicate="within")

# Compute potential_capacity_kw per building: max_panels * panel_capacity_watts / 1000
joined["potential_capacity_kw"] = (
    joined["max_panels"] * joined["panel_capacity_watts"]
) / 1000.0

# Aggregate per precinct
agg = joined.groupby("precinct_id").agg(
    total_kwh_annual    =("max_panels_kwh_annual", "sum"),
    total_usable_area_m2=("max_array_area_m2",     "sum"),
    potential_capacity_kw=("potential_capacity_kw", "sum"),
).reset_index()

print(f"  Aggregated {len(agg)} precincts")

# Merge back into cbd_wgs84 (drop placeholder columns first to avoid _x/_y conflicts)
cbd_wgs84 = cbd_wgs84.drop(columns=["total_kwh_annual", "total_usable_area_m2"])
cbd_wgs84 = cbd_wgs84.merge(agg, on="precinct_id", how="left")

# adoption_gap_kw = potential - installed (already installed from CER)
cbd_wgs84["adoption_gap_kw"] = (
    cbd_wgs84["potential_capacity_kw"] - cbd_wgs84["installed_capacity_kw"]
).clip(lower=0)

# Keep only precincts that have solar data from the DB
cbd_wgs84 = cbd_wgs84[cbd_wgs84["total_kwh_annual"].notna()].reset_index(drop=True)
print(f"\nKept {len(cbd_wgs84)} precincts with solar data")

print(cbd_wgs84[["name", "total_kwh_annual", "total_usable_area_m2",
                  "installed_capacity_kw", "potential_capacity_kw", "adoption_gap_kw"]].to_string())

# Step 7: Export GeoJSON (for spatial join and map rendering)
cbd_wgs84.to_file("melbourne_cbd_precincts.geojson", driver="GeoJSON")
print("\nExported: melbourne_cbd_precincts.geojson")

# Step 8: Export CSV with geometry as WKT (for PostgreSQL import)
cbd_csv = cbd_wgs84.copy()
cbd_csv["geo_boundary"] = cbd_csv["geometry"].apply(lambda g: g.wkt)
cbd_csv.drop(columns=["geometry"]).to_csv("melbourne_cbd_precincts.csv", index=False)
print("Exported: melbourne_cbd_precincts.csv")

print("\nPreview:")
print(cbd_csv[["precinct_id", "name"]].to_string())

# Step 10: Update buildings table with precinct_id via spatial join
print("\n[10] Updating buildings.precinct_id...")
conn3 = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                         user=DB_USER, password=DB_PASSWORD)
cur3 = conn3.cursor()

psycopg2.extras.execute_batch(
    cur3,
    "UPDATE buildings SET precinct_id = %s WHERE structure_id = %s",
    [(int(row["precinct_id"]), int(row["structure_id"])) for _, row in joined.iterrows()],
    page_size=500,
)

conn3.commit()
cur3.close()
conn3.close()
print("Done — buildings.precinct_id updated")