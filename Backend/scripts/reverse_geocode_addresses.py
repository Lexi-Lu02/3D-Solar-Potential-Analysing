#!/usr/bin/env python3
"""
Batch reverse-geocode buildings and write results to solar_api_cache.address.
Processes all records where address is missing in a single run.

Usage:
    python scripts/reverse_geocode_addresses.py [--batch-size N] [--dry-run]

Requirements (install separately, not in pyproject.toml — offline/batch use only):
    pip install psycopg[binary] requests python-dotenv tqdm

Environment variables (same as the API):
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

Nominatim policy:
    - 1 request per second maximum (enforced by this script)
    - User-Agent must identify the application
    - Do not run against production Nominatim without approval
"""

from __future__ import annotations

import argparse
import logging
import os
import time
from typing import Any

import requests
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "FIT5120-3D-Solar-Potential-Analysing/1.0 (educational project)"
REQUEST_DELAY_S = 1.1  # Nominatim rate limit: 1 req/s (with 0.1s margin)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_conn():
    """Build a psycopg connection from environment variables."""
    import psycopg  # noqa: WPS433

    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def count_remaining(conn) -> int:
    """Return the number of solar_api_cache rows still missing an address."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM solar_api_cache WHERE address IS NULL OR address = ''"
        )
        return cur.fetchone()[0]


def fetch_all(conn, batch_size: int | None = None) -> list[dict[str, Any]]:
    """
    Fetch rows that still need geocoding from solar_api_cache.
    Uses center_lat / center_lng stored in the table directly — no JOIN needed.
    If batch_size is specified, only fetch the first N rows (useful for testing).
    """
    with conn.cursor() as cur:
        if batch_size:
            cur.execute(
                """
                SELECT structure_id, center_lat, center_lng
                FROM solar_api_cache
                WHERE address IS NULL OR address = ''
                ORDER BY structure_id
                LIMIT %s
                """,
                (batch_size,),
            )
        else:
            cur.execute(
                """
                SELECT structure_id, center_lat, center_lng
                FROM solar_api_cache
                WHERE address IS NULL OR address = ''
                ORDER BY structure_id
                """,
            )
        rows = cur.fetchall()

    return [{"structure_id": r[0], "lat": r[1], "lng": r[2]} for r in rows]


def flush_batch(conn, updates: list[tuple[str, int]], dry_run: bool = False) -> None:
    """
    Write geocoded addresses back to solar_api_cache.
    `updates` is a list of (address, structure_id) tuples.
    """
    if dry_run:
        for address, structure_id in updates:
            logger.info("[DRY RUN] structure_id=%s → %s", structure_id, address)
        return

    with conn.cursor() as cur:
        cur.executemany(
            "UPDATE solar_api_cache SET address = %s WHERE structure_id = %s",
            updates,
        )
    conn.commit()
    logger.debug("Committed %d address updates.", len(updates))


# ---------------------------------------------------------------------------
# Nominatim
# ---------------------------------------------------------------------------

def reverse_geocode(lat: float, lng: float) -> str | None:
    """
    Call Nominatim reverse geocoding and return a display address string,
    or None on failure.
    """
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={
                "lat": lat,
                "lon": lng,
                "format": "jsonv2",
                "zoom": 18,          # street / house-number level
                "addressdetails": 0,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("display_name")
    except Exception as exc:
        logger.warning("Nominatim request failed for (%s, %s): %s", lat, lng, exc)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Limit the number of rows to process (default: no limit, process all). Useful for testing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be written without committing to the DB",
    )
    args = parser.parse_args()

    # Load .env if present (dev convenience)
    try:
        from dotenv import load_dotenv  # noqa: WPS433
        load_dotenv()
    except ImportError:
        pass

    logger.info("=" * 60)
    logger.info("Reverse geocoding script starting")
    logger.info("Rate limit: %.1fs/row | Mode: %s | Batch limit: %s",
                REQUEST_DELAY_S,
                "DRY RUN" if args.dry_run else "live write",
                f"{args.batch_size} rows" if args.batch_size else "none (process all)")
    logger.info("=" * 60)

    logger.info("Connecting to database...")
    conn = _get_conn()
    logger.info("Connected (host=%s, db=%s)",
                os.environ.get("DB_HOST"), os.environ.get("DB_NAME"))

    try:
        logger.info("Counting rows to process...")
        remaining = count_remaining(conn)
        logger.info("Rows missing address in solar_api_cache: %d", remaining)

        if remaining == 0:
            logger.info("All records already have addresses. Nothing to do.")
            return

        estimated_seconds = remaining * REQUEST_DELAY_S
        logger.info("Estimated time: %.0f seconds (%.1f minutes)",
                    estimated_seconds, estimated_seconds / 60)

        logger.info("Fetching rows from database...")
        batch = fetch_all(conn, batch_size=args.batch_size)
        logger.info("Fetched %d rows. Starting Nominatim calls...", len(batch))
        logger.info("-" * 60)

        succeeded = 0
        skipped = 0
        total_start = time.monotonic()

        with tqdm(total=len(batch), unit="row", dynamic_ncols=True) as pbar:
            for i, row in enumerate(batch):
                request_start = time.monotonic()

                pbar.set_description(f"structure_id={row['structure_id']}")

                address = reverse_geocode(row["lat"], row["lng"])

                if address:
                    # Write immediately after each success so progress is not lost on interruption
                    flush_batch(conn, [(address, row["structure_id"])], dry_run=args.dry_run)
                    succeeded += 1
                    tqdm.write(f"✓ [{row['structure_id']}] {address}")
                else:
                    skipped += 1
                    tqdm.write(f"✗ [{row['structure_id']}] No address returned, skipping")

                pbar.set_postfix(succeeded=succeeded, skipped=skipped)
                pbar.update(1)

                # Use actual elapsed time to calculate remaining wait,
                # ensuring at least REQUEST_DELAY_S between requests
                if i < len(batch) - 1:
                    elapsed = time.monotonic() - request_start
                    wait = max(0.0, REQUEST_DELAY_S - elapsed)
                    if wait > 0:
                        time.sleep(wait)

        total_elapsed = time.monotonic() - total_start
        total_minutes = total_elapsed / 60

        logger.info("-" * 60)
        logger.info("Done. Succeeded: %d, Skipped: %d, Total: %d",
                    succeeded, skipped, len(batch))
        logger.info("Total time: %.0f seconds (%.1f minutes)", total_elapsed, total_minutes)
        logger.info("=" * 60)

    finally:
        conn.close()
        logger.info("Database connection closed.")


if __name__ == "__main__":
    main()
