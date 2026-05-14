"""
POST /api/v1/ai/chat
POST /api/v1/ai/report

The frontend keeps the full conversation in localStorage and POSTs the whole
transcript on every request. The backend is stateless (no DB writes for AI),
truncates the history to a token budget, runs the Qwen tool loop, and
returns the assistant's reply plus a redacted tool trace for debugging.

Rate limiting: per-IP via slowapi, configurable through `AI_RATE_LIMIT_PER_MINUTE`.

Note: we deliberately do NOT use `from __future__ import annotations` here -
FastAPI introspects body-model annotations at app creation time and needs
real class references, not stringified forward refs.
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


# Resolved at import time. Changing AI_RATE_LIMIT_PER_MINUTE at runtime
# requires a process restart - acceptable for our deployment model.
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
# Both routes are gated on AI_DEBUG_LOG to avoid leaking prompts/replies in
# production. They are intentionally NOT rate-limited (operator tooling).

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
    """
    Reports do not carry conversation history. We synthesise a single user
    message describing what the report should cover, then let the model use
    its tools to gather data and emit the Markdown.
    """
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
