#!/usr/bin/env python3
"""
Batch reverse-geocode buildings and write results to solar_api_cache.address.

Usage:
    python scripts/reverse_geocode_addresses.py [--batch-size N] [--dry-run]

Requirements (install separately, not in pyproject.toml — offline/batch use only):
    pip install psycopg[binary] requests python-dotenv

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "FIT5120-3D-Solar-Potential-Analysing/1.0 (educational project)"
REQUEST_DELAY_S = 1.0  # Nominatim rate limit: 1 req/s


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


def fetch_batch(conn, batch_size: int) -> list[dict[str, Any]]:
    """
    Return up to `batch_size` rows that still need geocoding.
    JOIN with buildings to get lat/lng (solar_api_cache has center_lat/lng too,
    but buildings.lat/lng is the authoritative centroid used by the frontend).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT sac.structure_id, b.lat, b.lng
            FROM solar_api_cache sac
            JOIN buildings b ON b.structure_id = sac.structure_id
            WHERE sac.address IS NULL OR sac.address = ''
            ORDER BY sac.structure_id
            LIMIT %s
            """,
            (batch_size,),
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
    logger.info("Committed %d address updates.", len(updates))


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
        default=100,
        help="Number of rows to process per run (default: 100)",
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

    conn = _get_conn()
    try:
        remaining = count_remaining(conn)
        logger.info("Addresses remaining to geocode: %d", remaining)

        if remaining == 0:
            logger.info("Nothing to do.")
            return

        batch = fetch_batch(conn, args.batch_size)
        logger.info("Processing batch of %d rows.", len(batch))

        updates: list[tuple[str, int]] = []
        for i, row in enumerate(batch):
            address = reverse_geocode(row["lat"], row["lng"])
            if address:
                updates.append((address, row["structure_id"]))
                logger.debug(
                    "[%d/%d] structure_id=%s → %s",
                    i + 1, len(batch), row["structure_id"], address,
                )
            else:
                logger.warning(
                    "[%d/%d] structure_id=%s — no address returned, skipping",
                    i + 1, len(batch), row["structure_id"],
                )

            if i < len(batch) - 1:
                time.sleep(REQUEST_DELAY_S)

        if updates:
            flush_batch(conn, updates, dry_run=args.dry_run)
        else:
            logger.warning("No addresses were geocoded successfully.")

        logger.info("Done. Processed %d / %d rows.", len(updates), len(batch))

    finally:
        conn.close()


if __name__ == "__main__":
    main()
