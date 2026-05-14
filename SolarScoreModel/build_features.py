"""Step 1+2 (train): validate 2015 footprint CSV, then assemble training dataset.

A: validate + load footprint CSV → GeoDataFrame
B: spatial-join green_roof_solar patches → labels per struct_id
C: geometric features
D: neighbour shading proxy features
E: write dataset_2015.parquet (labelled) + dataset_2015_full.parquet

(fetch_data.py has been merged into this script; no separate data-fetch step needed.)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape as shapely_shape
from shapely.geometry.base import BaseGeometry

from _features import (
    compute_geometric_features,
    compute_neighbour_features,
)

# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
RAW_2015 = DATA_DIR / "raw_2015"
FOOTPRINT_CSV = RAW_2015 / "footprints" / "building-outlines-2015.csv"

SOLAR_SHP = (
    HERE.parent
    / "Data wrangling"
    / "green roof solar data"
    / "mga55_gda95_green_roof_solar.shp"
)

LABELS_OUT = DATA_DIR / "labels_2015.parquet"
DATASET_LABELED = DATA_DIR / "dataset_2015.parquet"
DATASET_FULL = DATA_DIR / "dataset_2015_full.parquet"

CRS_LATLNG = "EPSG:4326"
CRS_MGA55 = "EPSG:28355"  # matches green_roof_solar shp

RATING_MAP = {"Excellent": 5, "Good": 4, "Moderate": 3, "Poor": 2, "Very Poor": 1}
MIN_PATCH_AREA_M2 = 4.0  # drop noise patches

ID_COL = "struct_id"

EXPECTED_COLS = {"Geo Point", "Geo Shape", "geom_type", "ovlhgt_ahd", "suburb", "struct_id", "base_ahd"}


def validate_footprint(df: pd.DataFrame) -> None:
    """Sanity-check 2015 building outlines CSV columns and Geo Shape JSON."""
    missing = EXPECTED_COLS - set(df.columns)
    extra = set(df.columns) - EXPECTED_COLS
    if missing:
        sys.exit(f"[ERROR] missing columns in footprint CSV: {sorted(missing)}")
    if extra:
        print(f"    [warn] unexpected extra columns (ignored): {sorted(extra)}")

    n_geom_present = df["Geo Shape"].notna().sum()
    sample = df["Geo Shape"].dropna().sample(min(20, n_geom_present), random_state=0)
    bad_json = sum(
        1 for s in sample
        if not (lambda o: "coordinates" in o and "type" in o)(json.loads(s))
        if json.loads(s) is not None
    )
    if bad_json:
        print(f"    [warn] {bad_json}/{len(sample)} Geo Shape entries failed JSON parse")

    print(f"    rows total: {len(df)}  |  "
          f"Building rows: {(df['geom_type'] == 'Building').sum()}  |  "
          f"unique struct_id: {df['struct_id'].nunique()}")


def load_footprint() -> gpd.GeoDataFrame:
    print("[A] validating + loading 2015 footprint CSV ...")
    if not FOOTPRINT_CSV.exists():
        sys.exit(f"[ERROR] footprint CSV not found: {FOOTPRINT_CSV}")
    df_raw = pd.read_csv(FOOTPRINT_CSV, encoding="utf-8-sig")
    validate_footprint(df_raw)
    df = df_raw[df_raw["geom_type"] == "Building"].copy()
    print(f"    {len(df)} Building rows")

    geoms: list[BaseGeometry | None] = []
    for s in df["Geo Shape"]:
        try:
            geoms.append(shapely_shape(json.loads(s)))
        except (TypeError, ValueError, json.JSONDecodeError):
            geoms.append(None)
    df["geometry"] = geoms
    df = df[df["geometry"].notna()].copy()

    pt = df["Geo Point"].str.split(",", n=1, expand=True)
    df["lat"] = pt[0].astype(float)
    df["lng"] = pt[1].astype(float)

    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_LATLNG).to_crs(CRS_MGA55)

    # multi-part buildings: dissolve polygons sharing same struct_id
    n_rows_before = len(gdf)
    agg = (
        gdf.dissolve(by="struct_id", aggfunc={
            "ovlhgt_ahd": "max",
            "base_ahd": "min",
            "suburb": "first",
            "lat": "mean",
            "lng": "mean",
        }).reset_index()
    )
    print(f"    dissolved {n_rows_before} rows -> {len(agg)} buildings (by struct_id)")

    # derive standardised cols expected by _features.compute_geometric_features
    agg["building_height_m"] = (
        pd.to_numeric(agg["ovlhgt_ahd"], errors="coerce")
        - pd.to_numeric(agg["base_ahd"], errors="coerce")
    )
    agg["roof_top_elevation_m"] = pd.to_numeric(agg["ovlhgt_ahd"], errors="coerce")
    return agg


def build_labels(footprint: gpd.GeoDataFrame) -> pd.DataFrame:
    print("[B] generating 2015 labels from green_roof_solar.shp ...")
    if not SOLAR_SHP.exists():
        sys.exit(f"[ERROR] solar shapefile not found: {SOLAR_SHP}")

    patches = gpd.read_file(SOLAR_SHP)
    if patches.crs is None:
        patches.set_crs(CRS_MGA55, inplace=True)
    patches = patches.to_crs(CRS_MGA55)

    if "RATING" not in patches.columns:
        sys.exit(f"[ERROR] expected 'RATING' column in {SOLAR_SHP.name}")
    patches["solar_score"] = patches["RATING"].map(RATING_MAP)
    patches = patches.dropna(subset=["solar_score"])
    patches["solar_score"] = patches["solar_score"].astype(int)

    if "Shape_Area" not in patches.columns:
        patches["Shape_Area"] = patches.geometry.area
    patches = patches[patches["Shape_Area"] >= MIN_PATCH_AREA_M2].copy()
    print(f"    {len(patches)} solar patches after cleaning")

    joined = gpd.sjoin(
        patches[["solar_score", "Shape_Area", "geometry"]],
        footprint[["struct_id", "geometry"]],
        predicate="intersects",
        how="inner",
    )
    # patch overlapping multiple buildings → keep first (matches MelSolar.py behaviour)
    joined = joined[~joined.index.duplicated(keep="first")]
    print(f"    {joined['struct_id'].nunique()} unique buildings have ≥1 patch")

    labels = (
        joined.groupby("struct_id").agg(
            solar_score_avg=("solar_score", "mean"),
            roof_patch_count=("solar_score", "size"),
            total_patch_area_m2=("Shape_Area", "sum"),
        ).reset_index()
    )
    labels["solar_score_avg"] = labels["solar_score_avg"].round(3)
    labels["total_patch_area_m2"] = labels["total_patch_area_m2"].round(2)

    LABELS_OUT.parent.mkdir(parents=True, exist_ok=True)
    labels.to_parquet(LABELS_OUT, index=False)
    print(f"    -> {LABELS_OUT}  ({len(labels)} rows)")
    return labels


def main() -> None:
    print("=== Step 1+2: build_features (2015 training data) ===\n")

    fp = load_footprint()
    labels = build_labels(fp)

    print("[C] computing geometric features ...")
    geom_feat = compute_geometric_features(fp, id_col=ID_COL)
    print(f"    {len(geom_feat)} rows; "
          f"missing height: {geom_feat['building_height_m'].isna().sum()}")

    print("[D] computing neighbour shading proxy ...")
    nbr_feat = compute_neighbour_features(geom_feat, id_col=ID_COL)
    print(f"    {len(nbr_feat)} rows; "
          f"avg neighbours within 100m: {nbr_feat['nbr_count_100m'].mean():.1f}")

    full = (
        geom_feat
        .merge(nbr_feat, on=ID_COL, how="left")
        .merge(labels, on=ID_COL, how="left")
    )

    DATASET_FULL.parent.mkdir(parents=True, exist_ok=True)
    full.to_parquet(DATASET_FULL, index=False)
    print(f"\n[F] full dataset: {DATASET_FULL}  "
          f"({len(full)} rows, {full['solar_score_avg'].notna().sum()} labelled)")

    labelled = full[full["solar_score_avg"].notna()].copy()
    labelled.to_parquet(DATASET_LABELED, index=False)
    print(f"    labelled subset (training set): {DATASET_LABELED}  "
          f"({len(labelled)} rows)")


if __name__ == "__main__":
    main()
