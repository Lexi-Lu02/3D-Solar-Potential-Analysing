"""
Pydantic response models. Adding new endpoints means adding a model here.

Why duplicate the shape vs. dumping a raw dict from psycopg:
  1. FastAPI uses these to drive /docs (Swagger UI) — they ARE the API contract
  2. They strip out any column we accidentally SELECTed but don't want exposed
  3. They give the frontend a stable shape even if the DB schema shifts
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "error"] = Field(..., description="Overall service health")
    db: Literal["ok", "unreachable"] = Field(..., description="Database connectivity")
    buildings_count: int = Field(
        ..., ge=0, description="Number of rows currently in the buildings table"
    )
