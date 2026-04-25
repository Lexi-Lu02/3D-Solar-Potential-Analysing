"""
Global exception handlers.

Goal: never leak a Python traceback or psycopg error string to a client.
Every unhandled exception becomes a generic JSON envelope with a request ID
that can be cross-referenced against server logs. This is Risk R5
(configuration / information disclosure) from the project report.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def _envelope(
    error: str,
    request_id: str,
    status_code: int,
    detail: str | None = None,
) -> JSONResponse:
    body: dict[str, object] = {"error": error, "request_id": request_id}
    if detail:
        body["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        # 4xx is the client's fault — safe to echo the message back.
        return _envelope(
            error=_slug_for_status(exc.status_code),
            request_id=request_id,
            status_code=exc.status_code,
            detail=str(exc.detail) if exc.detail else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        # Pydantic errors include field paths — useful for the frontend dev.
        return _envelope(
            error="validation_error",
            request_id=request_id,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc.errors()),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        # Log the full traceback server-side, return only the request_id to
        # the caller. Operators can grep journalctl for the request_id.
        logger.exception(
            "Unhandled exception (request_id=%s) on %s %s",
            request_id, request.method, request.url.path,
        )
        return _envelope(
            error="internal_error",
            request_id=request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _slug_for_status(code: int) -> str:
    return {
        400: "bad_request",
        404: "not_found",
        422: "validation_error",
        429: "rate_limited",
        500: "internal_error",
        503: "service_unavailable",
    }.get(code, "error")
