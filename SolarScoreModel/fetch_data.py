"""Step 1: validate 2015 footprint CSV."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
RAW_2015 = DATA_DIR / "raw_2015"
FOOTPRINT_CSV = RAW_2015 / "footprints" / "building-outlines-2015.csv"

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
    """Read + sanity-check 2015 building outlines CSV."""
    if not FOOTPRINT_CSV.exists():
        sys.exit(
            f"[ERROR] footprint CSV not found at {FOOTPRINT_CSV}\n"
            f"        place building-outlines-2015.csv there"
        )

    df = pd.read_csv(FOOTPRINT_CSV, encoding="utf-8-sig")
    n_total = len(df)

    missing = EXPECTED_COLS - set(df.columns)
    extra = set(df.columns) - EXPECTED_COLS
    if missing:
        sys.exit(f"[ERROR] missing columns: {sorted(missing)}")
    if extra:
        print(f"[warn] unexpected extra columns (ignored): {sorted(extra)}")

    n_buildings = (df["geom_type"] == "Building").sum()
    n_struct_id_unique = df["struct_id"].nunique()
    n_geom_present = df["Geo Shape"].notna().sum()

    # spot-check Geo Shape JSON parsing
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

    print(f"[footprint] rows total         : {n_total}")
    print(f"[footprint] geom_type=Building  : {n_buildings}")
    print(f"[footprint] unique struct_id    : {n_struct_id_unique}")
    print(f"[footprint] Geo Shape non-null  : {n_geom_present}")
    return df


def main() -> None:
    print("=== Step 1: fetch_data ===\n")
    validate_footprint()
    print("\ndone.")


if __name__ == "__main__":
    main()
