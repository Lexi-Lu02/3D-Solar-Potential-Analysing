import psycopg2
import psycopg2.extras
import numpy as np


DB_HOST     = "3.26.146.10"
DB_PORT     = 5432           # SSH tunnel port
DB_NAME     = "melbourne_solar"
DB_USER     = "teamuser"
DB_PASSWORD = "123456"

ALPHA = 0.5                  # weight for quality vs quantity


def minmax_norm(arr: np.ndarray) -> np.ndarray:
    """Clip to 1st–99th percentile before normalising to reduce outlier impact."""
    low  = np.nanpercentile(arr, 1)
    high = np.nanpercentile(arr, 99)
    clipped = np.clip(arr, low, high)
    if high == low:
        return np.full_like(arr, 50.0, dtype=float)
    return (clipped - low) / (high - low) * 100.0


def main() -> None:
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Step 1: Drop old building_scores table (if exists), then create solar_score.
    print("[1] Dropping building_scores (if exists) and creating solar_score...")
    cur.execute("DROP TABLE IF EXISTS building_scores")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS solar_score (
            structure_id     INTEGER PRIMARY KEY,

            -- raw (un-normalised) metric values kept for auditing
            quality_raw      NUMERIC(10, 4),   -- sunshine hours / roof area m²
            quantity_raw     NUMERIC(12, 4),   -- annual kWh output

            -- normalised 0–100 components
            quality_norm     NUMERIC(6, 2),
            quantity_norm    NUMERIC(6, 2),

            -- final composite score 0–100
            composite_score  NUMERIC(6, 2),

            -- alpha recorded so we know how the score was weighted
            alpha            NUMERIC(3, 2),

            computed_at      TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()

    # Step 2: Pull all buildings from solar_api_cache that have the two
    #         fields we need.  Rows where either field is NULL or area is
    #         zero are skipped — they cannot produce a meaningful score.
    print("[2] Reading from solar_api_cache...")
    cur.execute("""
        SELECT
            structure_id,
            max_sunshine_hours_per_year,
            whole_roof_area_m2,
            max_panels_kwh_annual
        FROM solar_api_cache
        WHERE max_sunshine_hours_per_year IS NOT NULL
          AND whole_roof_area_m2          IS NOT NULL
          AND whole_roof_area_m2          > 0
          AND max_panels_kwh_annual       IS NOT NULL
    """)
    rows = cur.fetchall()
    print(f"  {len(rows)} buildings with complete data")

    if not rows:
        print("No data available — exiting.")
        cur.close()
        conn.close()
        return

    # Step 3: Compute raw metrics as numpy arrays for vectorised maths.
    print("[3] Computing quality and quantity metrics...")

    structure_ids = np.array([r["structure_id"] for r in rows])

    # Quality: sunshine intensity per m² — independent of building size.
    quality_raw = np.array([
        r["max_sunshine_hours_per_year"] / r["whole_roof_area_m2"]
        for r in rows
    ], dtype=float)

    # Quantity: raw annual electricity output in kWh.
    quantity_raw = np.array([r["max_panels_kwh_annual"] for r in rows], dtype=float)

    # Step 4: Normalise both metrics to 0–100.
    print("[4] Normalising metrics (log1p transform + 1st–99th percentile clip, then 0–100)...")
    quality_norm  = minmax_norm(np.log1p(quality_raw))
    quantity_norm = minmax_norm(np.log1p(quantity_raw))

    # Weighted combination, then re-normalise to stretch composite to full 0–100
    composite_raw = ALPHA * quality_norm + (1.0 - ALPHA) * quantity_norm
    composite = minmax_norm(composite_raw)

    # Step 5: Upsert into solar_score.
    print("[5] Upserting into solar_score...")
    upsert_data = [
        (
            int(structure_ids[i]),
            round(float(quality_raw[i]),   4),
            round(float(quantity_raw[i]),  4),
            round(float(quality_norm[i]),  2),
            round(float(quantity_norm[i]), 2),
            round(float(composite[i]),     2),
            float(ALPHA),
        )
        for i in range(len(structure_ids))
    ]

    psycopg2.extras.execute_batch(
        cur,
        """
        INSERT INTO solar_score
            (structure_id,
             quality_raw, quantity_raw,
             quality_norm, quantity_norm,
             composite_score, alpha)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (structure_id) DO UPDATE SET
            quality_raw     = EXCLUDED.quality_raw,
            quantity_raw    = EXCLUDED.quantity_raw,
            quality_norm    = EXCLUDED.quality_norm,
            quantity_norm   = EXCLUDED.quantity_norm,
            composite_score = EXCLUDED.composite_score,
            alpha           = EXCLUDED.alpha,
            computed_at     = NOW()
        """,
        upsert_data,
        page_size=500,
    )
    conn.commit()

    # Step 6: Print a quick summary.
    print(f"\nDone — {len(upsert_data)} rows written to solar_score")
    print(f"\nScore summary  (alpha={ALPHA}):")
    print(f"  quality_norm   mean={quality_norm.mean():.1f}  "
          f"min={quality_norm.min():.1f}  max={quality_norm.max():.1f}")
    print(f"  quantity_norm  mean={quantity_norm.mean():.1f}  "
          f"min={quantity_norm.min():.1f}  max={quantity_norm.max():.1f}")
    print(f"  composite      mean={composite.mean():.1f}  "
          f"min={composite.min():.1f}  max={composite.max():.1f}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
