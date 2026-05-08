"""
扩展特征版本 v2 ——在 v1（dataset_2015_full.parquet）基础上加入"邻居遮挡代理"特征 (Plan A)。

每栋建筑在 50 m / 100 m 半径内：
- 邻居数量
- 邻居最高高度
- 邻居平均高度
- 比自己更高的邻居数量
- "遮挡指数"：sum(max(neighbor_height - self_height, 0) / max(distance_m, 1))
  距离越近、高差越大，对自己越遮挡

这些都是确定性几何运算，零主观参数。半径 50m 与 100m 是两个常见量纲（街区/街区群），
都保留下来让模型自己决定哪个有用。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
DATASET_FULL = DATA_DIR / "dataset_2015_full.parquet"
OUT_FULL = DATA_DIR / "dataset_2015_v2_full.parquet"
OUT_LABELED = DATA_DIR / "dataset_2015_v2.parquet"

# 经度 1° 在墨尔本(纬度 -37.8) 约 88 km；纬度 1° 约 111 km。
# 用平均的 100 km 量级换算成半径 (m → 度) 的近似。
DEG_PER_M_LAT = 1.0 / 111_000.0
DEG_PER_M_LNG = 1.0 / 88_000.0
RADII_M = [50.0, 100.0]


def main() -> None:
    if not DATASET_FULL.exists():
        sys.exit(f"[ERROR] {DATASET_FULL} not found; run build_features.py first")

    df = pd.read_parquet(DATASET_FULL)
    print(f"[v2] loaded {len(df)} buildings from v1 dataset")

    # 用经纬度建 KD-Tree。墨尔本 CBD 几公里尺度上经度需要按 cos(lat) 缩放，否则
    # 东西向距离会偏大。把 lat/lng 投到米空间近似（local equirectangular）。
    lat = df["lat"].to_numpy()
    lng = df["lng"].to_numpy()
    h = df["building_height_m"].to_numpy()
    cos_lat = np.cos(np.deg2rad(np.nanmean(lat)))
    x_m = (lng - lng.mean()) * (1.0 / DEG_PER_M_LNG) * cos_lat
    y_m = (lat - lat.mean()) * (1.0 / DEG_PER_M_LAT)

    tree = cKDTree(np.column_stack([x_m, y_m]))

    out_cols: dict[str, np.ndarray] = {}
    n = len(df)
    for r in RADII_M:
        cnt = np.zeros(n, dtype=int)
        max_h = np.zeros(n)
        mean_h = np.zeros(n)
        taller_cnt = np.zeros(n, dtype=int)
        shading = np.zeros(n)

        # 一次性查询所有点的邻居
        idxs_per_pt = tree.query_ball_point(np.column_stack([x_m, y_m]), r)
        for i, idxs in enumerate(idxs_per_pt):
            # 排除自己
            idxs = [j for j in idxs if j != i]
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
            # shading index：高差除以距离（避免 0）
            shading[i] = float(np.sum(excess / np.clip(nbr_d, 1.0, None)))

        out_cols[f"nbr_count_{int(r)}m"] = cnt
        out_cols[f"nbr_max_height_{int(r)}m"] = max_h
        out_cols[f"nbr_mean_height_{int(r)}m"] = mean_h
        out_cols[f"nbr_taller_count_{int(r)}m"] = taller_cnt
        out_cols[f"nbr_shading_index_{int(r)}m"] = shading
        print(f"  radius={int(r)}m: avg neighbours = {cnt.mean():.1f}, "
              f"max shading_index = {shading.max():.2f}")

    extra = pd.DataFrame(out_cols, index=df.index)
    full = pd.concat([df, extra], axis=1)
    full.to_parquet(OUT_FULL, index=False)
    labelled = full[full["solar_score_avg"].notna()].copy()
    labelled.to_parquet(OUT_LABELED, index=False)

    print(f"\n[v2] full   -> {OUT_FULL}  ({len(full)} rows)")
    print(f"[v2] labelled -> {OUT_LABELED}  ({len(labelled)} rows)")
    print(f"[v2] new feature columns: {list(extra.columns)}")


if __name__ == "__main__":
    main()
