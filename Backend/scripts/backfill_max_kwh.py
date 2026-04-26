"""
Backfill min_panels_kwh_annual and max_panels_kwh_annual for rows in solar_api_cache.

This script:
  1. Fetches all structure_ids where max_panels_kwh_annual IS NULL
  2. Calls Google Solar API using center_lat/center_lng already stored in the table
  3. Extracts solarPanelConfigs[0].yearlyEnergyDcKwh  -> min_panels_kwh_annual
             solarPanelConfigs[-1].yearlyEnergyDcKwh -> max_panels_kwh_annual
  4. UPDATEs both columns (leaves everything else untouched)

Usage:
    python backfill_max_kwh.py

Config is read from the same .env file as the backend.
"""

import os
import time
import httpx
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST       = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT       = int(os.getenv("DB_PORT", "5433"))
DB_NAME       = os.getenv("DB_NAME", "melbourne_solar")
DB_USER       = os.getenv("DB_USER", "teamuser")
DB_PASSWORD   = os.getenv("DB_PASSWORD", "123456")
SOLAR_API_KEY = os.getenv("SOLAR_API_KEY", "AIzaSyDGQMGC6DzCGojtx9l559KX-qS2c4wbPT8")

SOLAR_BASE    = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
DELAY_SECONDS = 0.3
TIMEOUT       = 20
BATCH_SIZE    = 9000   # max rows to process in one run


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )


def get_pending(conn) -> list[tuple[int, float, float]]:
    """Return (structure_id, center_lat, center_lng) for rows missing max_panels_kwh_annual."""
    cur = conn.cursor()
    cur.execute("""
        SELECT structure_id, center_lat, center_lng
        FROM solar_api_cache
        WHERE max_panels_kwh_annual IS NULL
        LIMIT %s
    """, (BATCH_SIZE,))
    rows = cur.fetchall()
    cur.close()
    return rows


def fetch_kwh(client: httpx.Client, lat: float, lng: float) -> tuple[float | None, float | None]:
    """Call Google Solar API and return (min_kwh, max_kwh) from panel configs."""
    resp = client.get(SOLAR_BASE, params={
        "location.latitude":  lat,
        "location.longitude": lng,
        "requiredQuality":    "LOW",
        "key":                SOLAR_API_KEY,
    }, timeout=TIMEOUT)
    resp.raise_for_status()
    configs = resp.json().get("solarPotential", {}).get("solarPanelConfigs", [])
    if not configs:
        return None, None
    min_kwh = configs[0].get("yearlyEnergyDcKwh")
    max_kwh = configs[-1].get("yearlyEnergyDcKwh")
    return min_kwh, max_kwh


def update_row(conn, structure_id: int, min_kwh: float | None, max_kwh: float | None):
    cur = conn.cursor()
    cur.execute(
        """UPDATE solar_api_cache
           SET min_panels_kwh_annual = %s,
               max_panels_kwh_annual = %s
           WHERE structure_id = %s""",
        (min_kwh, max_kwh, structure_id)
    )
    conn.commit()
    cur.close()


def main():
    conn = get_conn()
    pending = get_pending(conn)
    print(f"[DB] {len(pending)} rows need backfill")

    if not pending:
        print("Nothing to do.")
        conn.close()
        return

    ok = skipped = failed = 0

    with httpx.Client() as client:
        for i, (sid, lat, lng) in enumerate(pending, 1):
            try:
                min_kwh, max_kwh = fetch_kwh(client, lat, lng)
                if max_kwh is not None:
                    update_row(conn, sid, min_kwh, max_kwh)
                    ok += 1
                    print(f"[{i}/{len(pending)}] structure_id={sid}  ✓ min={min_kwh:.1f}  max={max_kwh:.1f} kWh/yr")
                else:
                    skipped += 1
                    print(f"[{i}/{len(pending)}] structure_id={sid}  - no configs returned")
            except Exception as e:
                failed += 1
                print(f"[{i}/{len(pending)}] structure_id={sid}  ✗ {e}")

            time.sleep(DELAY_SECONDS)

    conn.close()
    print(f"\nDone!  updated={ok}  skipped={skipped}  failed={failed}")


if __name__ == "__main__":
    main()

    # --- Post-backfill: add max_kwh_source column and mark rows ---
    conn2 = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur2 = conn2.cursor()

    print("[post-1] Adding max_kwh_source column...")
    cur2.execute("ALTER TABLE solar_api_cache ADD COLUMN IF NOT EXISTS max_kwh_source VARCHAR(20)")

    print("[post-2] Marking existing rows as 'api'...")
    cur2.execute("UPDATE solar_api_cache SET max_kwh_source = 'api' WHERE max_panels_kwh_annual IS NOT NULL")

    print("[post-3] Estimating missing max_panels_kwh_annual...")
    cur2.execute("""
        UPDATE solar_api_cache
        SET
            max_panels_kwh_annual = max_panels * panel_capacity_watts * max_sunshine_hours_per_year / 1000,
            max_kwh_source = 'estimated'
        WHERE
            max_panels_kwh_annual IS NULL
            AND max_panels IS NOT NULL
            AND panel_capacity_watts IS NOT NULL
            AND max_sunshine_hours_per_year IS NOT NULL
    """)
    print(f"  Estimated {cur2.rowcount} rows")

    cur2.execute("SELECT COUNT(*) FROM solar_api_cache WHERE max_panels_kwh_annual IS NULL")
    print(f"  Remaining nulls: {cur2.fetchone()[0]}")

    conn2.commit()
    cur2.close()
    conn2.close()
    print("Done")
