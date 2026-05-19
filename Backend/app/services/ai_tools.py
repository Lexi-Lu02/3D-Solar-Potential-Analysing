"""
Tool functions exposed to the LLM via OpenAI-compatible function calling.

Design rules:
- Reuse service-layer functions where possible; new queries use parameterised
  SQL with whitelisted columns/values - no interpolation of user input.
- Tools return plain JSON-serialisable data.
- Input validated by a Pydantic model, rendered to JSONSchema for `tools`.
- Hard LIMIT cap so a hallucinated `limit=10000` can't drag the DB.

`dispatch_tool` runs inside the AI service's tool loop.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from psycopg import Connection
from psycopg.rows import dict_row
from pydantic import BaseModel, Field, ValidationError

from ..sql import load
from . import building_query, precinct_query

logger = logging.getLogger(__name__)

# hard cap on every list-returning tool, whatever the model asks for
GLOBAL_LIST_LIMIT = 20


# =============================================================================
# Pydantic input models — one per tool
# =============================================================================


class GetBuildingByIdArgs(BaseModel):
    id: int = Field(..., description="The building surrogate primary key (buildings.id).")


class SearchBuildingsArgs(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Substring to match against the building address (case-insensitive).",
    )


class TopBuildingsArgs(BaseModel):
    metric: Literal["solar_score", "usable_area", "annual_kwh"] = Field(
        "solar_score",
        description=(
            "Ranking metric. "
            "'solar_score' uses rooftop_solar.solar_score_avg (1-5 survey scale); "
            "'usable_area' uses rooftop_solar.usable_roof_area (m^2); "
            "'annual_kwh' uses solar_api_cache.max_panels_kwh_annual (Google Solar API). "
            "Buildings without data for the chosen metric are excluded automatically."
        ),
    )
    limit: int = Field(
        5, ge=1, le=GLOBAL_LIST_LIMIT, description="How many buildings to return (max 20)."
    )


class GetPrecinctByIdArgs(BaseModel):
    precinct_id: int = Field(..., description="The precinct surrogate id.")


class ListPrecinctsArgs(BaseModel):
    sort: Literal["kwh", "area", "buildings", "gap"] = Field(
        "kwh",
        description="Sort key: kwh=total annual generation, area=usable rooftop area, "
        "buildings=count of buildings, gap=adoption gap (potential minus installed).",
    )
    limit: int = Field(10, ge=1, le=GLOBAL_LIST_LIMIT)


class EmptyArgs(BaseModel):
    """For tools that take no arguments."""

    pass


# =============================================================================
# Tool implementations
# =============================================================================


def _get_building_by_id(conn: Connection, args: GetBuildingByIdArgs) -> dict[str, Any]:
    try:
        resp = building_query.fetch_building(conn, args.id)
    except building_query.BuildingNotFound:
        return {"found": False, "id": args.id}

    # drop heavyweight geometry - LLM doesn't need polygon coords
    payload = resp.model_dump(exclude={"geometry"})
    payload["found"] = True
    return payload


def _search_buildings(conn: Connection, args: SearchBuildingsArgs) -> dict[str, Any]:
    items = building_query.search_buildings(conn, args.query)
    return {
        "query": args.query,
        "count": len(items),
        "results": [item.model_dump() for item in items[:GLOBAL_LIST_LIMIT]],
    }


# metric -> ORDER BY expression. keys match the Literal in TopBuildingsArgs;
# values are server-side only, so no injection.
_TOP_BUILDINGS_METRIC: dict[str, str] = {
    "solar_score": "s.solar_score_avg",
    "usable_area": "s.usable_roof_area",
    "annual_kwh": "sac.max_panels_kwh_annual",
}


def _get_top_buildings(conn: Connection, args: TopBuildingsArgs) -> dict[str, Any]:
    """Top N buildings by a whitelisted metric. ORDER BY column comes from a
    server-side dict (no SQL injection via `metric`), LIMIT is a clamped int.
    NULL-metric rows are excluded so the model needn't reason about "no data"."""
    order_col = _TOP_BUILDINGS_METRIC[args.metric]
    sql = f"""
        SELECT
            b.id,
            b.structure_id,
            b.lat,
            b.lng,
            sac.address,
            s.solar_score_avg,
            s.usable_roof_area,
            s.dominant_rating,
            sac.max_panels_kwh_annual
        FROM buildings b
        LEFT JOIN rooftop_solar s ON s.structure_id = b.structure_id
        LEFT JOIN solar_api_cache sac ON sac.structure_id = b.structure_id
        WHERE {order_col} IS NOT NULL
        ORDER BY {order_col} DESC NULLS LAST
        LIMIT %(limit)s
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, {"limit": args.limit})
        rows = cur.fetchall()

    def _f(v: Any) -> float | None:
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    return {
        "metric": args.metric,
        "count": len(rows),
        "results": [
            {
                "id": int(r["id"]),
                "structure_id": int(r["structure_id"]),
                "lat": _f(r.get("lat")),
                "lng": _f(r.get("lng")),
                "address": r.get("address"),
                "solar_score_avg": _f(r.get("solar_score_avg")),
                "usable_roof_area_m2": _f(r.get("usable_roof_area")),
                "dominant_rating": r.get("dominant_rating"),
                "annual_kwh": _f(r.get("max_panels_kwh_annual")),
            }
            for r in rows
        ],
    }


def _get_precinct_by_id(conn: Connection, args: GetPrecinctByIdArgs) -> dict[str, Any]:
    try:
        detail = precinct_query.fetch_precinct(conn, args.precinct_id)
    except precinct_query.PrecinctNotFound:
        return {"found": False, "precinct_id": args.precinct_id}

    # strip heavyweight geo_boundary for the model
    payload = detail.model_dump(exclude={"geo_boundary"})
    payload["found"] = True
    return payload


def _list_top_precincts(conn: Connection, args: ListPrecinctsArgs) -> dict[str, Any]:
    summaries = precinct_query.list_precincts(conn, args.sort)
    return {
        "sort": args.sort,
        "count": min(len(summaries), args.limit),
        "results": [s.model_dump() for s in summaries[: args.limit]],
    }


def _get_dataset_stats(conn: Connection, _: EmptyArgs) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(load("buildings_stats"))
        row = cur.fetchone() or {}

    def _f(v: Any) -> float:
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    return {
        "total_buildings": int(row.get("total_buildings") or 0),
        "usable_area_m2": _f(row.get("usable_area_m2")),
        "kwh_annual_total": _f(row.get("kwh_annual")),
        "high_potential_count": int(row.get("high_potential_count") or 0),
    }


def _get_schema_overview(_conn: Connection, _: EmptyArgs) -> dict[str, Any]:
    """Static description, exposed as a tool so the model can re-read it."""
    from .ai_prompts import SCHEMA_DESCRIPTION

    return {"schema": SCHEMA_DESCRIPTION}


# =============================================================================
# Tool registry
# =============================================================================


class _ToolSpec:
    """Internal wrapper - everything needed to expose one tool."""

    def __init__(
        self,
        name: str,
        description: str,
        args_model: type[BaseModel],
        handler,
    ):
        self.name = name
        self.description = description
        self.args_model = args_model
        self.handler = handler

    def openai_schema(self) -> dict[str, Any]:
        """Render as one entry of OpenAI's `tools` array."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.args_model.model_json_schema(),
            },
        }


_TOOL_SPECS: list[_ToolSpec] = [
    _ToolSpec(
        name="get_building_by_id",
        description=(
            "Look up a single building by its database id (buildings.id, an integer). "
            "Returns location, height, roof type, solar score, usable roof area, and "
            "address (if known). Returns found=false when the id is not in the DB."
        ),
        args_model=GetBuildingByIdArgs,
        handler=_get_building_by_id,
    ),
    _ToolSpec(
        name="search_buildings_by_address",
        description=(
            "Search buildings whose address contains the given substring "
            "(case-insensitive). Returns up to 20 matches with id, structure_id, "
            "lat/lng and address. Use this when the user names a street or building."
        ),
        args_model=SearchBuildingsArgs,
        handler=_search_buildings,
    ),
    _ToolSpec(
        name="get_top_buildings",
        description=(
            "Return the top N buildings ranked by a metric (solar_score or "
            "usable_area). Use this for 'best' / 'highest score' / 'biggest roof' "
            "style questions. Limit is capped at 20."
        ),
        args_model=TopBuildingsArgs,
        handler=_get_top_buildings,
    ),
    _ToolSpec(
        name="get_precinct_by_id",
        description=(
            "Look up one precinct (neighbourhood) by its precinct_id. Returns name, "
            "postcode, total annual kWh, installed/potential capacity, adoption gap, "
            "and building count."
        ),
        args_model=GetPrecinctByIdArgs,
        handler=_get_precinct_by_id,
    ),
    _ToolSpec(
        name="list_top_precincts",
        description=(
            "List precincts ranked by a metric. sort=kwh ranks by total annual kWh, "
            "area=usable rooftop area, buildings=building count, gap=potential minus "
            "installed (development opportunity). Use this for 'which precinct is "
            "best for development' style questions."
        ),
        args_model=ListPrecinctsArgs,
        handler=_list_top_precincts,
    ),
    _ToolSpec(
        name="get_dataset_stats",
        description=(
            "Return city-wide aggregates: total buildings, total usable roof area, "
            "total annual kWh potential, count of high-potential buildings. Use this "
            "for 'overall' / 'city total' questions."
        ),
        args_model=EmptyArgs,
        handler=_get_dataset_stats,
    ),
    _ToolSpec(
        name="get_schema_overview",
        description=(
            "Return a short description of the database tables and the units used. "
            "Call this if you are unsure what data is available."
        ),
        args_model=EmptyArgs,
        handler=_get_schema_overview,
    ),
]


# Public surface --------------------------------------------------------------

TOOL_REGISTRY: dict[str, _ToolSpec] = {spec.name: spec for spec in _TOOL_SPECS}

OPENAI_TOOLS: list[dict[str, Any]] = [spec.openai_schema() for spec in _TOOL_SPECS]


class ToolExecutionError(Exception):
    """Raised when a tool call cannot be executed (bad args, missing tool, ...)."""


def dispatch_tool(conn: Connection, name: str, arguments_json: str) -> str:
    """
    Execute one LLM tool call, return the result as a JSON string to feed
    back as a `tool` message.

    - Unknown tool -> error dict (no exception bubbles up, model can retry).
    - Pydantic validation error -> structured error message.
    - DB error -> caught + logged, error dict returned; never leak raw
      exception text to the model.
    """
    spec = TOOL_REGISTRY.get(name)
    if spec is None:
        logger.warning("LLM tried to call unknown tool: %s", name)
        return json.dumps({"error": f"unknown tool: {name}"})

    try:
        args = spec.args_model.model_validate_json(arguments_json or "{}")
    except ValidationError as ve:
        logger.info("Tool %s rejected invalid args: %s", name, ve.errors())
        return json.dumps(
            {
                "error": "invalid_arguments",
                "details": [
                    {"loc": list(e["loc"]), "msg": e["msg"]} for e in ve.errors()
                ],
            }
        )

    try:
        result = spec.handler(conn, args)
    except Exception as exc:
        logger.exception("Tool %s failed with unexpected error", name)

        # CRITICAL: roll back. psycopg leaves an aborted transaction after a
        # SQL error and every later query on the same conn raises
        # InFailedSqlTransaction. one request shares ONE conn across tools,
        # so a poisoned tool would cascade-fail all the rest (seen on EC2).
        try:
            conn.rollback()
        except Exception:
            logger.exception("Failed to roll back connection after %s error", name)

        # with AI_DEBUG_LOG on, surface the exception summary in the result
        # so the debug UI shows the real reason - never the full traceback,
        # never anything when debug is off.
        from ..config import get_settings
        payload: dict[str, Any] = {"error": "tool_execution_failed", "tool": name}
        if get_settings().ai_debug_log:
            payload["exception"] = type(exc).__name__
            payload["message"] = str(exc)[:500]
        return json.dumps(payload)

    try:
        return json.dumps(result, default=str)
    except (TypeError, ValueError):
        logger.exception("Tool %s returned unserialisable result", name)
        return json.dumps({"error": "serialisation_failed", "tool": name})
