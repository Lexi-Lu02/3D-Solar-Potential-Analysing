"""
PostgreSQL connection pool wired into FastAPI's lifespan.

The pool is opened once at app startup, closed at shutdown, and individual
requests borrow a connection via the `get_conn` dependency. We use
`psycopg_pool.ConnectionPool` (sync) because every endpoint we plan to ship is
a single-shot SELECT — async wouldn't buy us anything for this workload, but
would force every handler to be `async def`.

To keep the rest of the code testable, the pool lives on `app.state.db_pool`
rather than as a module-level global.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import Request
from psycopg import Connection
from psycopg_pool import ConnectionPool

from .config import get_settings

logger = logging.getLogger(__name__)


def build_pool() -> ConnectionPool:
    """Construct (but do not open) a connection pool from settings."""
    settings = get_settings()
    pool = ConnectionPool(
        conninfo=settings.db_conninfo,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        open=False,
        # Sanity-check every borrowed connection. Cheap, and avoids handing a
        # dead socket to a request handler after PG bounces.
        check=ConnectionPool.check_connection,
        name="solarmap-api-pool",
    )
    return pool


@contextmanager
def lifespan_pool(pool: ConnectionPool) -> Iterator[ConnectionPool]:
    """Open the pool, yield it, then close it. Used by FastAPI's lifespan."""
    logger.info("Opening DB connection pool")
    pool.open(wait=True, timeout=10.0)
    try:
        yield pool
    finally:
        logger.info("Closing DB connection pool")
        pool.close()


def get_conn(request: Request) -> Iterator[Connection]:
    """
    FastAPI dependency: borrow one connection from the pool for the request.

    The connection is returned to the pool automatically when the request
    finishes, regardless of whether the handler raised.
    """
    pool: ConnectionPool = request.app.state.db_pool
    with pool.connection() as conn:
        yield conn
