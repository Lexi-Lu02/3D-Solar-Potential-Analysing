"""
Step 1: 数据获取与校验。

- 校验用户已下载的 2015 building outlines CSV（列、行数、几何字段）
- 从 NASA POWER 拉 2015 全年 daily 全天空向下短波辐照（ALLSKY_SFC_SW_DWN），
  覆盖 Melbourne CBD bbox 的格点（含小 buffer），缓存到本地

不做任何主观加权或筛选；只做"该数据源是否可读"的最小校验，以及把外部 API
原样落盘到磁盘。
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# 路径常量（全部相对本文件，便于在任何工作目录调用）
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
RAW_2015 = DATA_DIR / "raw_2015"
FOOTPRINT_CSV = RAW_2015 / "footprints" / "building-outlines-2015.csv"
NASA_DIR = RAW_2015 / "nasa_power"
NASA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 校验 footprint CSV
# ---------------------------------------------------------------------------
EXPECTED_COLS = {
    "Geo Point",
    "Geo Shape",
    "geom_type",
    "ovlhgt_ahd",
    "suburb",
    "struct_id",
    "base_ahd",
}


def validate_footprint() -> pd.DataFrame:
    """读取 + 严格校验 building outlines 2015 CSV。"""
    if not FOOTPRINT_CSV.exists():
        sys.exit(
            f"[ERROR] footprint CSV not found at {FOOTPRINT_CSV}\n"
            f"        请把 building-outlines-2015.csv 放到该路径"
        )

    # utf-8-sig 处理 BOM；csv 列里含 JSON，pandas 默认引擎能正确解析
    df = pd.read_csv(FOOTPRINT_CSV, encoding="utf-8-sig")
    n_total = len(df)

    missing = EXPECTED_COLS - set(df.columns)
    extra = set(df.columns) - EXPECTED_COLS
    if missing:
        sys.exit(f"[ERROR] missing columns: {sorted(missing)}")
    if extra:
        print(f"[warn] unexpected extra columns (will ignore): {sorted(extra)}")

    n_buildings = (df["geom_type"] == "Building").sum()
    n_struct_id_unique = df["struct_id"].nunique()
    n_geom_present = df["Geo Shape"].notna().sum()

    # 抽样校验 Geo Shape 是合法 JSON
    sample = df["Geo Shape"].dropna().sample(min(20, n_geom_present), random_state=0)
    bad_json = 0
    for s in sample:
        try:
            obj = json.loads(s)
            if "coordinates" not in obj or "type" not in obj:
                bad_json += 1
        except json.JSONDecodeError:
            bad_json += 1
    if bad_json:
        print(f"[warn] {bad_json}/{len(sample)} Geo Shape entries failed JSON parse")

    print(f"[footprint] rows total      : {n_total}")
    print(f"[footprint] geom_type=Building : {n_buildings}")
    print(f"[footprint] unique struct_id   : {n_struct_id_unique}")
    print(f"[footprint] Geo Shape non-null : {n_geom_present}")
    return df


# ---------------------------------------------------------------------------
# NASA POWER 拉取
# ---------------------------------------------------------------------------
NASA_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_PARAMETERS = "ALLSKY_SFC_SW_DWN"  # 全天空向下短波辐照，单位 kWh/m²/day
NASA_COMMUNITY = "RE"                  # Renewable Energy
START_DATE = "20150101"
END_DATE = "20151231"

# CBD bbox 含 buffer（包含周边 suburb 以保 KD-Tree 边界点）
# Melbourne CBD: lat -37.78..-37.83, lng 144.92..145.00
LAT_MIN, LAT_MAX = -37.86, -37.76
LNG_MIN, LNG_MAX = 144.88, 145.04

# NASA POWER 原生分辨率约 0.5°，但 API 端会对小范围请求做插值。
# 用 0.05° (~5 km) 步长拉一个网格，KD-Tree 能给每栋建筑唯一的最近邻；
# 即使返回值在 CBD 内差异不大，也保留这个粒度方便未来切换更高分辨率源。
GRID_STEP = 0.05


def grid_points() -> list[tuple[float, float]]:
    """返回 (lat, lng) 列表，覆盖 CBD bbox。"""
    pts: list[tuple[float, float]] = []
    lat = LAT_MIN
    while lat <= LAT_MAX + 1e-9:
        lng = LNG_MIN
        while lng <= LNG_MAX + 1e-9:
            pts.append((round(lat, 4), round(lng, 4)))
            lng += GRID_STEP
        lat += GRID_STEP
    return pts


def fetch_one_point(lat: float, lng: float) -> Path:
    """拉一个格点的 2015 全年 daily 辐照，缓存为 CSV。已存在则跳过。"""
    out_path = NASA_DIR / f"power_{lat:+.4f}_{lng:+.4f}.csv"
    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"  [skip] cached: {out_path.name}")
        return out_path

    params = {
        "parameters": NASA_PARAMETERS,
        "community": NASA_COMMUNITY,
        "longitude": f"{lng:.4f}",
        "latitude": f"{lat:.4f}",
        "start": START_DATE,
        "end": END_DATE,
        "format": "JSON",
    }

    for attempt in range(1, 4):
        try:
            r = requests.get(NASA_URL, params=params, timeout=60)
            r.raise_for_status()
            payload = r.json()
            break
        except (requests.RequestException, ValueError) as e:
            print(f"  [retry {attempt}/3] {lat},{lng}: {e}")
            time.sleep(2 ** attempt)
    else:
        sys.exit(f"[ERROR] NASA POWER fetch failed at ({lat},{lng})")

    daily = payload["properties"]["parameter"][NASA_PARAMETERS]
    fill = payload.get("header", {}).get("fill_value", -999)
    rows = [
        {"date": d, "kwh_m2_day": v}
        for d, v in daily.items()
        if v != fill and v is not None
    ]
    if not rows:
        sys.exit(f"[ERROR] no valid daily values returned for ({lat},{lng})")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "kwh_m2_day"])
        w.writeheader()
        w.writerows(rows)
    print(f"  [ok]   {out_path.name} ({len(rows)} days)")
    return out_path


def fetch_nasa_power() -> None:
    pts = grid_points()
    print(f"[nasa] grid: {len(pts)} points "
          f"(lat {LAT_MIN}..{LAT_MAX}, lng {LNG_MIN}..{LNG_MAX}, step {GRID_STEP})")
    for (lat, lng) in pts:
        fetch_one_point(lat, lng)

    # 写一份索引方便后续 build_features.py 直接读
    index_rows = [
        {
            "lat": lat,
            "lng": lng,
            "csv": f"power_{lat:+.4f}_{lng:+.4f}.csv",
        }
        for (lat, lng) in pts
    ]
    idx_path = NASA_DIR / "index.csv"
    with idx_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["lat", "lng", "csv"])
        w.writeheader()
        w.writerows(index_rows)
    print(f"[nasa] index written to {idx_path}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== Step 1: fetch_data ===")
    print()

    print("--- A. validate footprint CSV ---")
    validate_footprint()
    print()

    print("--- B. fetch NASA POWER 2015 ---")
    fetch_nasa_power()
    print()

    print("done.")


if __name__ == "__main__":
    main()
