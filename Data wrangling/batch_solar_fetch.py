import time
import httpx
import psycopg2

# --- Config ---
API_BASE      = "http://localhost:8000/api/v1"
DB_HOST       = "127.0.0.1"
DB_PORT       = 5433           # SSH tunnel port
DB_NAME       = "melbourne_solar"
DB_USER       = "teamuser"
DB_PASSWORD   = "123456"

BATCH_SIZE    = 2000         # how many buildings to process
DELAY_SECONDS = 0.3            # delay between requests (avoid rate limiting)
TIMEOUT       = 20            # seconds per request


def get_structure_ids(limit: int) -> list[int]:
    """Fetch unique structure_ids from buildings table."""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT b.structure_id
        FROM buildings b
        WHERE b.structure_id NOT IN (
            SELECT structure_id FROM solar_api_cache
        )
        LIMIT %s
    """, (limit,))
    ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    print(f"[DB] Found {len(ids)} buildings not yet cached")
    return ids


def fetch_solar(client: httpx.Client, structure_id: int) -> str:
    """Call the solar endpoint and return source ('api' or 'cache')."""
    url = f"{API_BASE}/buildings/{structure_id}/solar"
    resp = client.get(url, timeout=TIMEOUT)
    if resp.status_code == 200:
        return resp.json().get("source", "unknown")
    elif resp.status_code == 404:
        return "not_found"
    else:
        return f"error_{resp.status_code}"


def main():
    ids = get_structure_ids(BATCH_SIZE)

    if not ids:
        print("All buildings already cached — nothing to do.")
        return

    success = 0
    failed  = 0
    skipped = 0

    with httpx.Client() as client:
        for i, sid in enumerate(ids, 1):
            try:
                source = fetch_solar(client, sid)

                if source == "api":
                    success += 1
                    status = "✓ cached"
                elif source == "cache":
                    skipped += 1
                    status = "↩ already cached"
                elif source == "not_found":
                    skipped += 1
                    status = "✗ not found"
                else:
                    failed += 1
                    status = f"✗ {source}"

                print(f"[{i}/{len(ids)}] structure_id={sid}  {status}")

            except Exception as e:
                failed += 1
                print(f"[{i}/{len(ids)}] structure_id={sid}  ✗ exception: {e}")

            # Respect rate limit
            time.sleep(DELAY_SECONDS)

    print(f"\nDone!")
    print(f"  Newly cached : {success}")
    print(f"  Skipped      : {skipped}")
    print(f"  Failed       : {failed}")


if __name__ == "__main__":
    main()
