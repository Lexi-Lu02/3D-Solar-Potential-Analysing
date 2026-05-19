"""
AI chat/report endpoints.

Frontend POSTs the whole transcript every request - backend is stateless.
Truncate history, run the Qwen tool loop, return reply + redacted trace.
Per-IP rate limit via slowapi (AI_RATE_LIMIT_PER_MINUTE).

No `from __future__ import annotations` here - FastAPI needs real class
refs for body-model annotations, not stringified forward refs.
"""

import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from psycopg import Connection
from pydantic import BaseModel, Field

from ..config import get_settings
from ..db import get_conn
from ..rate_limit import limiter
from ..services.ai_context import ContextPayload
from ..services.ai_debug import DebugTrace, recorder
from ..services.ai_service import AIService, ToolTrace, get_ai_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


# resolved at import time - changing the limit needs a process restart
_LIMIT = f"{get_settings().ai_rate_limit_per_minute}/minute"


# --- Request / response schemas ---------------------------------------------


UserType = Literal["property_owner", "city_planner"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(
        ..., description="Only user/assistant turns; system prompt is server-side."
    )
    content: str = Field(..., min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=100)
    mode: Literal["chat", "report"] = Field("chat")
    user_type: UserType | None = Field(
        None,
        description=(
            "Persona picker from the frontend. 'property_owner' tailors tone "
            "and focus to one specific building's economics; 'city_planner' "
            "tilts toward precinct-level aggregates and policy framing. "
            "Omit (null) to let the assistant ask a clarifying question."
        ),
    )
    context: ContextPayload | None = Field(
        None,
        description=(
            "Trusted, pre-computed context the frontend wants the AI to use "
            "directly without calling tools to re-verify. Use this for the "
            "currently-selected building / precinct and any user-tweaked "
            "assumptions (electricity tariff, season, etc.). All fields are "
            "typed and bounded to prevent prompt injection through this path."
        ),
    )


class ReportRequest(BaseModel):
    target_type: Literal["building", "precinct"]
    target_id: int = Field(..., ge=1)
    focus: str | None = Field(None, max_length=200)
    audience: str | None = Field(None, max_length=200)
    user_type: UserType | None = Field(
        None,
        description="Same persona picker as /chat. Defaults to generic.",
    )
    context: ContextPayload | None = Field(
        None,
        description="Same trusted-context channel as /chat. See ChatRequest.context.",
    )


class ToolTraceOut(BaseModel):
    name: str
    arguments: str
    ok: bool


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolTraceOut]
    iterations: int
    blocked: bool
    block_reason: str | None = None


def _to_trace_out(traces: list[ToolTrace]) -> list[ToolTraceOut]:
    return [ToolTraceOut(name=t.name, arguments=t.arguments, ok=t.ok) for t in traces]


# --- Routes -----------------------------------------------------------------


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Multi-turn Q&A with the Solar Potential assistant.",
)
@limiter.limit(_LIMIT)
def chat(
    request: Request,
    body: ChatRequest,
    conn: Connection = Depends(get_conn),
    ai: AIService = Depends(get_ai_service),
) -> ChatResponse:
    if body.messages[-1].role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="last message must have role='user'",
        )

    messages = [m.model_dump() for m in body.messages]
    trace = DebugTrace(
        enabled=get_settings().ai_debug_log,
        request_id=getattr(request.state, "request_id", None),
    )
    trace.request_in(
        endpoint="/api/v1/ai/chat",
        mode=body.mode,
        user_type=body.user_type,
        messages=messages,
    )
    result = ai.chat(
        conn,
        messages,
        mode=body.mode,
        user_type=body.user_type,
        context=body.context,
        trace=trace,
    )

    return ChatResponse(
        reply=result.reply,
        tool_calls=_to_trace_out(result.tool_calls),
        iterations=result.iterations,
        blocked=result.blocked,
        block_reason=result.block_reason,
    )


# --- Debug viewer ----------------------------------------------------------
# all gated on AI_DEBUG_LOG so prod doesn't leak prompts/replies.
# not rate-limited - operator tooling.

_DEBUG_HTML_PATH = Path(__file__).resolve().parent.parent / "static" / "ai_debug.html"


def _require_debug_enabled() -> None:
    if not get_settings().ai_debug_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI debug viewer is disabled. Set AI_DEBUG_LOG=true in .env to enable.",
        )


@router.get(
    "/debug/traces",
    summary="Recent AI request traces (newest first). Gated on AI_DEBUG_LOG=true.",
    response_class=JSONResponse,
)
def debug_traces() -> JSONResponse:
    _require_debug_enabled()
    return JSONResponse({"traces": recorder.snapshot()})


@router.get(
    "/debug/ui",
    summary="HTML viewer for recent AI request traces. Gated on AI_DEBUG_LOG=true.",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def debug_ui() -> HTMLResponse:
    _require_debug_enabled()
    try:
        html = _DEBUG_HTML_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug UI template missing: {_DEBUG_HTML_PATH}",
        )
    return HTMLResponse(html)


@router.post(
    "/debug/clear",
    summary="Clear the in-memory trace buffer. Gated on AI_DEBUG_LOG=true.",
    response_class=JSONResponse,
)
def debug_clear() -> JSONResponse:
    _require_debug_enabled()
    recorder.clear()
    return JSONResponse({"cleared": True})


@router.post(
    "/report",
    response_model=ChatResponse,
    summary="Generate a structured Markdown report for one building or precinct.",
)
@limiter.limit(_LIMIT)
def report(
    request: Request,
    body: ReportRequest,
    conn: Connection = Depends(get_conn),
    ai: AIService = Depends(get_ai_service),
) -> ChatResponse:
    """No conversation history - synthesise one user message and let the
    model gather data via tools and emit the Markdown."""
    parts = [
        f"Generate a Markdown report for {body.target_type} id={body.target_id}.",
    ]
    if body.focus:
        parts.append(f"Focus: {body.focus}")
    if body.audience:
        parts.append(f"Intended audience: {body.audience}")
    parts.append(
        "Use your tools to fetch every number you cite. Follow the report "
        "structure given in the system prompt."
    )
    user_text = "\n".join(parts)

    messages = [{"role": "user", "content": user_text}]
    trace = DebugTrace(
        enabled=get_settings().ai_debug_log,
        request_id=getattr(request.state, "request_id", None),
    )
    trace.request_in(
        endpoint="/api/v1/ai/report",
        mode="report",
        user_type=body.user_type,
        messages=messages,
    )
    result = ai.chat(
        conn,
        messages=messages,
        mode="report",
        user_type=body.user_type,
        context=body.context,
        trace=trace,
    )

    return ChatResponse(
        reply=result.reply,
        tool_calls=_to_trace_out(result.tool_calls),
        iterations=result.iterations,
        blocked=result.blocked,
        block_reason=result.block_reason,
    )
