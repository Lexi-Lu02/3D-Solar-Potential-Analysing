"""
FastAPI application factory.

The app is fully read-only:
  - There are no POST/PUT/DELETE handlers.
  - The DB user (in production: solarmap_api_ro) only has SELECT.
  - All endpoints live under the /api/v1 prefix.

CORS is only enabled when the operator sets CORS_ORIGINS in the environment.
In production the frontend is served from the same nginx as the API, so the
browser sees same-origin requests and CORS is irrelevant.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .config import get_settings
from .db import build_pool, lifespan_pool
from .errors import register_error_handlers
from .routers import buildings, health, solar, solar_cache, sun, yield_engine

API_PREFIX = "/api/v1"


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open the DB pool on startup, close it on shutdown."""
    pool = build_pool()
    with lifespan_pool(pool):
        app.state.db_pool = pool
        yield
        # __exit__ closes the pool


def create_app() -> FastAPI:
    settings = get_settings()
    _configure_logging(settings.log_level)

    app = FastAPI(
        title="Solar Map API",
        version="0.1.0",
        description=(
            "Read-only API for the 3D Solar Potential Analysing project. "
            "Serves Melbourne CBD building footprints, solar suitability data, "
            "and per-building kWh estimates."
        ),
        lifespan=lifespan,
        # Pin docs under the API prefix so nginx only has to forward /api/*
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=f"{API_PREFIX}/redoc",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )

    # --- Rate limiting (R4: DoS / abuse) ---
    limiter = Limiter(key_func=get_remote_address, default_limits=[])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # --- CORS (only in dev / when explicitly configured) ---
    if settings.cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_methods=["GET"],
            allow_headers=["*"],
            allow_credentials=False,
        )

    # --- Per-request ID for log/error correlation ---
    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["x-request-id"] = request.state.request_id
        return response

    # --- Global error envelopes ---
    register_error_handlers(app)

    # --- Routers ---
    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(buildings.router, prefix=API_PREFIX)
    app.include_router(yield_engine.router, prefix=API_PREFIX)
    app.include_router(solar.router, prefix=API_PREFIX)
    app.include_router(solar_cache.router, prefix=API_PREFIX)
    app.include_router(sun.router, prefix=API_PREFIX)
    return app


app = create_app()
