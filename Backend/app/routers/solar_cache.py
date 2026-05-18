from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.db import get_conn

router = APIRouter()


@router.get("/buildings/{structure_id}/solar")
async def get_building_solar(structure_id: int, conn: Connection = Depends(get_conn)):
    """
    Return solar data for a building from the local cache only.
    Returns 404 if no cached data exists — the Google Solar API is not called.
    """
    row = conn.execute(
        "SELECT * FROM solar_api_cache WHERE structure_id = %s",
        (structure_id,)
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No solar data found for this building")

    return {"source": "cache", "data": dict(row)}
