"""Feature engineering primitives shared by train (2015) + infer (2023).

Input contract: GeoDataFrame / DataFrame with id_col, geometry (EPSG:28355),
lat, lng, building_height_m, roof_top_elevation_m, suburb.
"""

from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry.base import BaseGeometry


NEIGHBOUR_RADII_M = [50.0, 100.0]
# rough local equirectangular conversion at Melbourne lat
DEG_PER_M_LAT = 1.0 / 111_000.0
DEG_PER_M_LNG = 1.0 / 88_000.0


def _long_short_axis(g: BaseGeometry) -> tuple[float, float, float]:
    # min-rotated-rect: (long_edge_len, short_edge_len, long_edge_angle_deg in [0,180))
    if g.is_empty:
        return (0.0, 0.0, 0.0)
    rect = g.minimum_rotated_rectangle
    coords = list(rect.exterior.coords)[:4]
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


def compute_geometric_features(
    gdf: gpd.GeoDataFrame, id_col: str
) -> pd.DataFrame:
    """Roof geometry from EPSG:28355 polygons."""
    df = gdf.copy()

    df["roof_area_m2"] = df.geometry.area
    df["roof_perimeter_m"] = df.geometry.length

    # Polsby-Popper compactness ∈ (0,1]
    p = df["roof_perimeter_m"].to_numpy()
    a = df["roof_area_m2"].to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        df["roof_compactness"] = np.where(
            p > 0, 4 * math.pi * a / (p ** 2), 0.0
        )

    # min-rotated-rect axes → aspect angle + elongation
    long_short_aspect = df.geometry.apply(_long_short_axis)
    df["long_axis_m"] = [t[0] for t in long_short_aspect]
    df["short_axis_m"] = [t[1] for t in long_short_aspect]
    df["roof_aspect_deg"] = [t[2] for t in long_short_aspect]
    df["roof_elongation"] = np.where(
        df["short_axis_m"] > 0, df["long_axis_m"] / df["short_axis_m"], 1.0
    )

    keep = [
        id_col, "lat", "lng", "suburb",
        "roof_area_m2", "roof_perimeter_m", "roof_compactness",
        "building_height_m", "roof_top_elevation_m",
        "roof_aspect_deg", "roof_elongation",
    ]
    return df[keep].copy()


def sample_irradiance(
    geom_df: pd.DataFrame, id_col: str, nasa_dir: Path
) -> pd.DataFrame:
    """Nearest-grid-point NASA POWER lookup → annual / winter / summer / seasonality.

    Requires nasa_dir/index.csv + per-point CSVs (populated by fetch_data.py).
    """
    nasa_index = nasa_dir / "index.csv"
    if not nasa_index.exists():
        raise FileNotFoundError(
            f"missing {nasa_index}; run fetch_data.py to populate NASA POWER cache"
        )
    idx = pd.read_csv(nasa_index)
    annual: list[float] = []
    winter: list[float] = []
    summer: list[float] = []
    for _, row in idx.iterrows():
        daily = pd.read_csv(nasa_dir / row["csv"])
        daily["date"] = pd.to_datetime(daily["date"], format="%Y%m%d")
        v = daily["kwh_m2_day"].to_numpy()
        m = daily["date"].dt.month.to_numpy()
        annual.append(float(v.sum()))
        # southern hemisphere: winter Jun/Jul/Aug, summer Dec/Jan/Feb
        winter.append(float(v[np.isin(m, [6, 7, 8])].mean()))
        summer.append(float(v[np.isin(m, [12, 1, 2])].mean()))
    grid = idx.copy()
    grid["annual_solar_kwh_m2"] = annual
    grid["winter_solar_kwh_m2_day"] = winter
    grid["summer_solar_kwh_m2_day"] = summer
    grid["solar_seasonality"] = grid["summer_solar_kwh_m2_day"] / grid[
        "winter_solar_kwh_m2_day"
    ].replace(0, np.nan)

    tree = cKDTree(grid[["lat", "lng"]].to_numpy())
    _, nn = tree.query(geom_df[["lat", "lng"]].to_numpy(), k=1)

    out = geom_df[[id_col]].copy()
    out["annual_solar_kwh_m2"] = grid["annual_solar_kwh_m2"].to_numpy()[nn]
    out["winter_solar_kwh_m2_day"] = grid["winter_solar_kwh_m2_day"].to_numpy()[nn]
    out["summer_solar_kwh_m2_day"] = grid["summer_solar_kwh_m2_day"].to_numpy()[nn]
    out["solar_seasonality"] = grid["solar_seasonality"].to_numpy()[nn]
    return out


def compute_neighbour_features(
    geom_df: pd.DataFrame, id_col: str
) -> pd.DataFrame:
    """50m / 100m neighbour-shading proxy: count, max h, mean h, taller count, shading_index."""
    lat = geom_df["lat"].to_numpy()
    lng = geom_df["lng"].to_numpy()
    h = geom_df["building_height_m"].fillna(0).to_numpy()
    cos_lat = np.cos(np.deg2rad(np.nanmean(lat)))
    x_m = (lng - lng.mean()) * (1.0 / DEG_PER_M_LNG) * cos_lat
    y_m = (lat - lat.mean()) * (1.0 / DEG_PER_M_LAT)
    tree = cKDTree(np.column_stack([x_m, y_m]))

    out = geom_df[[id_col]].copy()
    n = len(geom_df)
    for r in NEIGHBOUR_RADII_M:
        cnt = np.zeros(n, dtype=int)
        max_h = np.zeros(n)
        mean_h = np.zeros(n)
        taller_cnt = np.zeros(n, dtype=int)
        shading = np.zeros(n)
        idxs_per_pt = tree.query_ball_point(np.column_stack([x_m, y_m]), r)
        for i, idxs in enumerate(idxs_per_pt):
            idxs = [j for j in idxs if j != i]  # drop self
            if not idxs:
                continue
            nbr_h = h[idxs]
            nbr_dx = x_m[idxs] - x_m[i]
            nbr_dy = y_m[idxs] - y_m[i]
            nbr_d = np.sqrt(nbr_dx * nbr_dx + nbr_dy * nbr_dy)
            cnt[i] = len(idxs)
            max_h[i] = float(np.nanmax(nbr_h))
            mean_h[i] = float(np.nanmean(nbr_h))
            excess = np.clip(nbr_h - h[i], 0.0, None)
            taller_cnt[i] = int((excess > 0).sum())
            # weighted by inverse distance (clip to ≥1m to avoid blowup)
            shading[i] = float(np.sum(excess / np.clip(nbr_d, 1.0, None)))
        out[f"nbr_count_{int(r)}m"] = cnt
        out[f"nbr_max_height_{int(r)}m"] = max_h
        out[f"nbr_mean_height_{int(r)}m"] = mean_h
        out[f"nbr_taller_count_{int(r)}m"] = taller_cnt
        out[f"nbr_shading_index_{int(r)}m"] = shading
    return out
