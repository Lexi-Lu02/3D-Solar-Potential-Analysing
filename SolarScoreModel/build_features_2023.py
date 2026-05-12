"""Step 2 (infer): build 2023 inference dataset from PG.

Pulls buildings + precincts, applies the same _features.* functions used at training,
writes dataset_2023.parquet for infer.py.

NASA POWER cache reused from training (constant within CBD; year-agnostic).
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape as shapely_shape
from shapely.geometry.base import BaseGeometry

from _db import get_connection
from _features import (
    compute_geometric_features,
    compute_neighbour_features,
)

# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
DATASET_2023 = DATA_DIR / "dataset_2023.parquet"

CRS_LATLNG = "EPSG:4326"
CRS_MGA55 = "EPSG:28355"

ID_COL = "structure_id"


def load_buildings_from_db() -> gpd.GeoDataFrame:
    """Pull buildings + precinct name → GeoDataFrame in EPSG:28355."""
    print("[A] connecting to PostgreSQL ...")
    conn = get_connection()
    sql = """
        SELECT
            b.structure_id,
            b.lat,
            b.lng,
            b.geo_shape,
            b.building_height,
            b.base_height,
            b.max_elevation,
            b.precinct_id,
            p.name AS precinct_name
        FROM buildings b
        LEFT JOIN precincts p ON p.precinct_id = b.precinct_id
        WHERE b.geo_shape IS NOT NULL
    """
    df = pd.read_sql(sql, conn)
    conn.close()
    print(f"    pulled {len(df)} buildings from DB")

    # parse geo_shape JSON
    geoms: list[BaseGeometry | None] = []
    for s in df["geo_shape"]:
        try:
            geoms.append(shapely_shape(json.loads(s)))
        except (TypeError, ValueError, json.JSONDecodeError):
            geoms.append(None)
    df["geometry"] = geoms
    df = df[df["geometry"].notna()].copy()

    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_LATLNG).to_crs(CRS_MGA55)

    # buildings table is row-per-polygon (40k rows / 19k distinct structure_id);
    # dissolve to one multi-polygon per building, mirroring 2015 footprint handling
    n_rows_before = len(gdf)
    gdf = (
        gdf.dissolve(by="structure_id", aggfunc={
            "lat": "mean",
            "lng": "mean",
            "building_height": "max",
            "base_height": "min",
            "max_elevation": "max",
            "precinct_id": "first",
            "precinct_name": "first",
        }).reset_index()
    )
    print(f"    dissolved {n_rows_before} rows -> {len(gdf)} buildings (by structure_id)")

    # derive standardised cols expected by _features.compute_geometric_features.
    # prefer DB's pre-computed building_height; fall back to max_elevation - base_height
    h_direct = pd.to_numeric(gdf["building_height"], errors="coerce")
    h_fallback = (
        pd.to_numeric(gdf["max_elevation"], errors="coerce")
        - pd.to_numeric(gdf["base_height"], errors="coerce")
    )
    gdf["building_height_m"] = h_direct.fillna(h_fallback)
    gdf["roof_top_elevation_m"] = pd.to_numeric(gdf["max_elevation"], errors="coerce")

    # train-time categorical was 2015 footprint.suburb (string).
    # 14 precinct names match those 14 suburb strings exactly → just rename.
    gdf["suburb"] = gdf["precinct_name"].fillna("UNKNOWN")

    print(f"    {gdf['precinct_name'].notna().sum()} have precinct "
          f"({100*gdf['precinct_name'].notna().sum()/len(gdf):.1f}%)")
    return gdf


def main() -> None:
    print("=== Step 2 (infer): build_features_2023 (from PG) ===\n")

    fp = load_buildings_from_db()

    print("[B] computing geometric features ...")
    geom_feat = compute_geometric_features(fp, id_col=ID_COL)
    print(f"    {len(geom_feat)} rows; "
          f"missing height: {geom_feat['building_height_m'].isna().sum()}")

    print("[C] computing neighbour shading proxy ...")
    nbr_feat = compute_neighbour_features(geom_feat, id_col=ID_COL)
    print(f"    {len(nbr_feat)} rows; "
          f"avg neighbours within 100m: {nbr_feat['nbr_count_100m'].mean():.1f}")

    # keep precinct_id + precinct_name for infer.py → solar_score table
    precinct_meta = fp[["structure_id", "precinct_id", "precinct_name"]].copy()

    full = (
        geom_feat
        .merge(nbr_feat, on=ID_COL, how="left")
        .merge(precinct_meta, on=ID_COL, how="left")
    )

    DATASET_2023.parent.mkdir(parents=True, exist_ok=True)
    full.to_parquet(DATASET_2023, index=False)
    print(f"\n[E] inference dataset: {DATASET_2023}  ({len(full)} rows)")
    print()
    print("suburb (from precincts.name) value counts:")
    print(full["suburb"].value_counts().to_string())


if __name__ == "__main__":
    main()
