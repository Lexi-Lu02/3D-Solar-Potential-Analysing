import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.db import get_conn
from app.services.solar_api import fetch_solar_from_google

router = APIRouter()

JSONB_COLS = {"whole_roof_sunshine_quantiles", "roof_segment_stats", "solar_panel_configs"}


@router.get("/buildings/{structure_id}/solar")
async def get_building_solar(structure_id: int, conn: Connection = Depends(get_conn)):
    """
    Return solar data for a building.
    Cache-aside: check DB first, call Google API if not found, then cache result.
    """

    # Step 1: check cache
    row = conn.execute(
        "SELECT * FROM solar_api_cache WHERE structure_id = %s",
        (structure_id,)
    ).fetchone()
    if row:
        return {"source": "cache", "data": dict(row)}

    # Step 2: get building coordinates
    building = conn.execute(
        "SELECT lat, lng FROM buildings WHERE structure_id = %s LIMIT 1",
        (structure_id,)
    ).fetchone()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    # Step 3: call Google Solar API
    try:
        solar_data = await fetch_solar_from_google(building[0], building[1])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Google Solar API error: {e}")

    # Step 4: write to cache
    now = datetime.utcnow()
    solar_data["structure_id"] = structure_id
    solar_data["fetched_at"]   = now
    solar_data["updated_at"]   = now

    for col in JSONB_COLS:
        if solar_data.get(col) is not None:
            solar_data[col] = json.dumps(solar_data[col])

    cols   = ", ".join(solar_data.keys())
    values = ", ".join(["%s"] * len(solar_data))
    conn.execute(
        f"INSERT INTO solar_api_cache ({cols}) VALUES ({values})",
        list(solar_data.values())
    )
    conn.commit()

    return {"source": "api", "data": solar_data}