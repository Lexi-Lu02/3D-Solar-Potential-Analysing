import geopandas as gpd
import pandas as pd
from shapely.geometry import box
import os

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
cbd_wgs84["adoption_gap_kw"] = None

# Step 5: Export GeoJSON (for spatial join and map rendering)
cbd_wgs84.to_file("melbourne_cbd_precincts.geojson", driver="GeoJSON")
print("\nExported: melbourne_cbd_precincts.geojson")

# Step 6: Export CSV with geometry as WKT (for PostgreSQL import)
cbd_csv = cbd_wgs84.copy()
cbd_csv["geo_boundary"] = cbd_csv["geometry"].apply(lambda g: g.wkt)
cbd_csv.drop(columns=["geometry"]).to_csv("melbourne_cbd_precincts.csv", index=False)
print("Exported: melbourne_cbd_precincts.csv")

print("\nPreview:")
print(cbd_csv[["precinct_id", "name"]].to_string())