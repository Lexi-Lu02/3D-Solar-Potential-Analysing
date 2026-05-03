"""
Step 2: 特征构建 + 2015 标签生成。

A. 加载 2015 footprint CSV → 解析 Geo Shape JSON → GeoDataFrame
B. 用 2015 green_roof_solar shp 与 footprint 做空间连接，按 struct_id
   聚合得到 solar_score_avg（1–5）作为标签
C. 几何特征：面积、周长、紧凑度、高度、屋顶绝对海拔、长轴方位角、
   长短轴比、质心 lat/lng、suburb
D. NASA POWER 辐照特征：用 KD-Tree 把每栋建筑的质心映射到最近格点，
   计算年度/冬季/夏季/季节性比值
E. 合并 → dataset_2015.parquet（仅有标签的）+ dataset_2015_full.parquet
   （含无标签建筑，供推理）

不做任何主观加权，仅做几何派生 + 标准的 sjoin/groupby + KD-Tree 最近邻。
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import shape as shapely_shape
from shapely.geometry.base import BaseGeometry

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
RAW_2015 = DATA_DIR / "raw_2015"
FOOTPRINT_CSV = RAW_2015 / "footprints" / "building-outlines-2015.csv"
NASA_DIR = RAW_2015 / "nasa_power"
NASA_INDEX = NASA_DIR / "index.csv"

# 2015 专家评分 patch shapefile（仓库已含）
SOLAR_SHP = (
    HERE.parent
    / "Data wrangling"
    / "green roof solar data"
    / "mga55_gda95_green_roof_solar.shp"
)

LABELS_OUT = DATA_DIR / "labels_2015.parquet"
DATASET_LABELED = DATA_DIR / "dataset_2015.parquet"
DATASET_FULL = DATA_DIR / "dataset_2015_full.parquet"

# 投影常量
CRS_LATLNG = "EPSG:4326"
CRS_MGA55 = "EPSG:28355"  # 与 green_roof_solar shp 一致

# 评分映射，与 [Data wrangling/MelSolar.py:46] 保持一致
RATING_MAP = {
    "Excellent": 5,
    "Good": 4,
    "Moderate": 3,
    "Poor": 2,
    "Very Poor": 1,
}

# 噪声 patch 阈值，与既有清洗规则一致
MIN_PATCH_AREA_M2 = 4.0


# ---------------------------------------------------------------------------
# A. 加载 footprint
# ---------------------------------------------------------------------------
def load_footprint() -> gpd.GeoDataFrame:
    print("[A] loading 2015 footprint CSV ...")
    df = pd.read_csv(FOOTPRINT_CSV, encoding="utf-8-sig")
    df = df[df["geom_type"] == "Building"].copy()
    print(f"    {len(df)} Building rows")

    geoms: list[BaseGeometry | None] = []
    for s in df["Geo Shape"]:
        try:
            geoms.append(shapely_shape(json.loads(s)))
        except (TypeError, ValueError, json.JSONDecodeError):
            geoms.append(None)
    df["geometry"] = geoms
    df = df[df["geometry"].notna()].copy()

    # 解析 Geo Point → lat / lng
    pt = df["Geo Point"].str.split(",", n=1, expand=True)
    df["lat"] = pt[0].astype(float)
    df["lng"] = pt[1].astype(float)

    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_LATLNG)
    # 重投影到 MGA55，方便与 solar shp 做 sjoin 与几何度量
    gdf = gdf.to_crs(CRS_MGA55)

    # 一栋建筑可能有多条 footprint 行（multi-part），按 struct_id 合并
    n_rows_before = len(gdf)
    agg = (
        gdf.dissolve(by="struct_id", aggfunc={
            "ovlhgt_ahd": "max",
            "base_ahd": "min",
            "suburb": "first",
            "lat": "mean",
            "lng": "mean",
        })
        .reset_index()
    )
    print(f"    dissolved {n_rows_before} rows -> {len(agg)} buildings (by struct_id)")
    return agg


# ---------------------------------------------------------------------------
# B. 重新生成 2015 标签
# ---------------------------------------------------------------------------
def build_labels(footprint: gpd.GeoDataFrame) -> pd.DataFrame:
    print("[B] generating 2015 labels from green_roof_solar.shp ...")
    if not SOLAR_SHP.exists():
        sys.exit(f"[ERROR] solar shapefile not found: {SOLAR_SHP}")

    patches = gpd.read_file(SOLAR_SHP)
    if patches.crs is None:
        patches.set_crs(CRS_MGA55, inplace=True)
    patches = patches.to_crs(CRS_MGA55)

    # 列名在 shp 里是 RATING / Shape_Area
    if "RATING" not in patches.columns:
        sys.exit(f"[ERROR] expected 'RATING' column in {SOLAR_SHP.name}; got {list(patches.columns)}")
    patches["solar_score"] = patches["RATING"].map(RATING_MAP)
    patches = patches.dropna(subset=["solar_score"])
    patches["solar_score"] = patches["solar_score"].astype(int)

    if "Shape_Area" not in patches.columns:
        patches["Shape_Area"] = patches.geometry.area
    patches = patches[patches["Shape_Area"] >= MIN_PATCH_AREA_M2].copy()
    print(f"    {len(patches)} solar patches after cleaning")

    # 空间连接：每个 patch 找到与之相交的建筑
    joined = gpd.sjoin(
        patches[["solar_score", "Shape_Area", "geometry"]],
        footprint[["struct_id", "geometry"]],
        predicate="intersects",
        how="inner",
    )
    # patch 与多栋楼相交时只保留第一栋（与 [MelSolar.py] 同处理）
    joined = joined[~joined.index.duplicated(keep="first")]

    print(f"    {joined['struct_id'].nunique()} unique buildings have ≥1 patch")

    labels = (
        joined.groupby("struct_id")
        .agg(
            solar_score_avg=("solar_score", "mean"),
            roof_patch_count=("solar_score", "size"),
            total_patch_area_m2=("Shape_Area", "sum"),
        )
        .reset_index()
    )
    labels["solar_score_avg"] = labels["solar_score_avg"].round(3)
    labels["total_patch_area_m2"] = labels["total_patch_area_m2"].round(2)

    LABELS_OUT.parent.mkdir(parents=True, exist_ok=True)
    labels.to_parquet(LABELS_OUT, index=False)
    print(f"    -> {LABELS_OUT}  ({len(labels)} rows)")
    return labels


# ---------------------------------------------------------------------------
# C. 几何特征
# ---------------------------------------------------------------------------
def _long_short_axis(g: BaseGeometry) -> tuple[float, float, float]:
    """返回 minimum-rotated-rectangle 的长轴长度、短轴长度、长轴方位角(度, 0-180)."""
    if g.is_empty:
        return (0.0, 0.0, 0.0)
    rect = g.minimum_rotated_rectangle
    coords = list(rect.exterior.coords)[:4]
    # 计算 4 条边长度，取最长一条与最短一条
    edges = []
    for i in range(4):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % 4]
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(dy, dx)) % 180.0
        edges.append((length, angle))
    long_edge = max(edges, key=lambda x: x[0])
    short_edge = min(edges, key=lambda x: x[0])
    return (long_edge[0], short_edge[0], long_edge[1])


def geometric_features(footprint: gpd.GeoDataFrame) -> pd.DataFrame:
    print("[C] computing geometric features ...")
    df = footprint.copy()

    df["roof_area_m2"] = df.geometry.area
    df["roof_perimeter_m"] = df.geometry.length

    # Polsby-Popper 紧凑度 = 4π·A / P²，∈ (0,1]，圆=1
    p = df["roof_perimeter_m"].to_numpy()
    a = df["roof_area_m2"].to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        compactness = np.where(p > 0, 4 * math.pi * a / (p ** 2), 0.0)
    df["roof_compactness"] = compactness

    df["building_height_m"] = (
        pd.to_numeric(df["ovlhgt_ahd"], errors="coerce")
        - pd.to_numeric(df["base_ahd"], errors="coerce")
    )
    df["roof_top_elevation_m"] = pd.to_numeric(df["ovlhgt_ahd"], errors="coerce")

    long_short_aspect = df.geometry.apply(_long_short_axis)
    df["long_axis_m"] = [t[0] for t in long_short_aspect]
    df["short_axis_m"] = [t[1] for t in long_short_aspect]
    df["roof_aspect_deg"] = [t[2] for t in long_short_aspect]
    df["roof_elongation"] = np.where(
        df["short_axis_m"] > 0, df["long_axis_m"] / df["short_axis_m"], 1.0
    )

    keep = [
        "struct_id",
        "lat",
        "lng",
        "suburb",
        "roof_area_m2",
        "roof_perimeter_m",
        "roof_compactness",
        "building_height_m",
        "roof_top_elevation_m",
        "roof_aspect_deg",
        "roof_elongation",
    ]
    out = df[keep].copy()
    print(f"    {len(out)} rows; missing height: "
          f"{out['building_height_m'].isna().sum()}")
    return out


# ---------------------------------------------------------------------------
# D. NASA POWER 辐照采样
# ---------------------------------------------------------------------------
def irradiance_features(geom_df: pd.DataFrame) -> pd.DataFrame:
    print("[D] sampling NASA POWER irradiance ...")
    if not NASA_INDEX.exists():
        sys.exit(f"[ERROR] missing {NASA_INDEX}; run fetch_data.py first")

    idx = pd.read_csv(NASA_INDEX)
    annual: list[float] = []
    winter: list[float] = []
    summer: list[float] = []
    for _, row in idx.iterrows():
        daily = pd.read_csv(NASA_DIR / row["csv"])
        daily["date"] = pd.to_datetime(daily["date"], format="%Y%m%d")
        v = daily["kwh_m2_day"].to_numpy()
        m = daily["date"].dt.month.to_numpy()
        annual.append(float(v.sum()))
        # 南半球：冬 6/7/8，夏 12/1/2
        winter.append(float(v[np.isin(m, [6, 7, 8])].mean()))
        summer.append(float(v[np.isin(m, [12, 1, 2])].mean()))
    grid = idx.copy()
    grid["annual_solar_kwh_m2"] = annual
    grid["winter_solar_kwh_m2_day"] = winter
    grid["summer_solar_kwh_m2_day"] = summer
    grid["solar_seasonality"] = grid["summer_solar_kwh_m2_day"] / grid[
        "winter_solar_kwh_m2_day"
    ].replace(0, np.nan)

    # KD-Tree 最近邻：用 lat/lng 直接做欧氏距离，CBD 范围内近似可用
    tree = cKDTree(grid[["lat", "lng"]].to_numpy())
    _, nn = tree.query(geom_df[["lat", "lng"]].to_numpy(), k=1)

    out = geom_df[["struct_id"]].copy()
    out["annual_solar_kwh_m2"] = grid["annual_solar_kwh_m2"].to_numpy()[nn]
    out["winter_solar_kwh_m2_day"] = grid["winter_solar_kwh_m2_day"].to_numpy()[nn]
    out["summer_solar_kwh_m2_day"] = grid["summer_solar_kwh_m2_day"].to_numpy()[nn]
    out["solar_seasonality"] = grid["solar_seasonality"].to_numpy()[nn]
    n_unique = out[
        ["annual_solar_kwh_m2", "winter_solar_kwh_m2_day", "summer_solar_kwh_m2_day"]
    ].drop_duplicates().shape[0]
    print(f"    {len(out)} buildings sampled; "
          f"{n_unique} unique irradiance combinations across CBD "
          f"(NASA POWER native resolution is coarse — limitation noted in REPORT)")
    return out


# ---------------------------------------------------------------------------
# E. 合并输出
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== Step 2: build_features ===\n")

    fp = load_footprint()
    labels = build_labels(fp)
    geom_feat = geometric_features(fp)
    irr_feat = irradiance_features(geom_feat)

    full = geom_feat.merge(irr_feat, on="struct_id", how="left")
    full = full.merge(labels, on="struct_id", how="left")

    DATASET_FULL.parent.mkdir(parents=True, exist_ok=True)
    full.to_parquet(DATASET_FULL, index=False)
    print(f"\n[E] full dataset (labels may be NaN): {DATASET_FULL}  "
          f"({len(full)} rows, {full['solar_score_avg'].notna().sum()} labelled)")

    labelled = full[full["solar_score_avg"].notna()].copy()
    labelled.to_parquet(DATASET_LABELED, index=False)
    print(f"    labelled subset (training set): {DATASET_LABELED}  "
          f"({len(labelled)} rows)")

    # 简短摘要
    print("\nfeature summary (labelled subset):")
    print(labelled.describe(include="all").T[["count", "mean", "std", "min", "max"]]
          .round(2).to_string())


if __name__ == "__main__":
    main()
