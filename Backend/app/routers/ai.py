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
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from psycopg import Connection
from pydantic import BaseModel, Field

from ..config import get_settings
from ..db import get_conn
from ..rate_limit import limiter
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


class ReportRequest(BaseModel):
    target_type: Literal["building", "precinct"]
    target_id: int = Field(..., ge=1)
    focus: str | None = Field(None, max_length=200)
    audience: str | None = Field(None, max_length=200)
    user_type: UserType | None = Field(
        None,
        description="Same persona picker as /chat. Defaults to generic.",
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
    result = ai.chat(conn, messages, mode=body.mode, user_type=body.user_type)

    return ChatResponse(
        reply=result.reply,
        tool_calls=_to_trace_out(result.tool_calls),
        iterations=result.iterations,
        blocked=result.blocked,
        block_reason=result.block_reason,
    )


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

    result = ai.chat(
        conn,
        messages=[{"role": "user", "content": user_text}],
        mode="report",
        user_type=body.user_type,
    )

    return ChatResponse(
        reply=result.reply,
        tool_calls=_to_trace_out(result.tool_calls),
        iterations=result.iterations,
        blocked=result.blocked,
        block_reason=result.block_reason,
    )
