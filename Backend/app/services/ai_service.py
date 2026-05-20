"""
Orchestrates one chat / report request end-to-end.

Flow: truncate history -> scrub input -> inject system prompt -> run the
DashScope (Qwen) tool loop -> deterministic output filter -> optional
self-critique -> return answer + redacted trace.

All sync, so it composes with the psycopg pool. The OpenAI client is sync too.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import time

import httpx
from openai import APIError, OpenAI
from psycopg import Connection

from ..config import Settings, get_settings
from . import ai_history, ai_safety
from .ai_context import ContextPayload, format_context
from .ai_debug import DebugTrace
from .ai_prompts import (
    REFUSAL_MESSAGE,
    SELF_CRITIQUE_PROMPT,
    UserType,
    get_system_prompt,
)
from .ai_tools import OPENAI_TOOLS, dispatch_tool

logger = logging.getLogger(__name__)


# --- Public response shape ---------------------------------------------------


@dataclass
class ToolTrace:
    """One tool call, redacted for the frontend (debug/audit)."""

    name: str
    arguments: str  # raw JSON from the model
    ok: bool


@dataclass
class AIResult:
    reply: str
    tool_calls: list[ToolTrace] = field(default_factory=list)
    iterations: int = 0
    blocked: bool = False
    block_reason: str | None = None


# --- The service -------------------------------------------------------------


class AIService:
    """Thin wrapper around the OpenAI-compatible Qwen client + tool loop."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        api_key = self.settings.dashscope_api_key.get_secret_value()
        if not api_key:
            # ok to construct without a key (tests, healthchecks); chat() fails loudly
            logger.warning("DASHSCOPE_API_KEY is empty; AI calls will fail until set.")
        # must beat nginx's 60s or we eat 504s - SDK default is 600s ("forever")
        self.client = OpenAI(
            api_key=api_key or "missing",
            base_url=self.settings.qwen_base_url,
            timeout=httpx.Timeout(
                self.settings.ai_call_timeout_seconds,
                connect=10.0,
            ),
            max_retries=1,
        )

    # --- Top-level entry points ---------------------------------------------

    def chat(
        self,
        conn: Connection,
        messages: list[dict],
        mode: Literal["chat", "report"] = "chat",
        user_type: UserType | None = None,
        context: ContextPayload | None = None,
        trace: DebugTrace | None = None,
    ) -> AIResult:
        """
        Run a chat or report request through the tool loop.

        `messages` - user/assistant transcript only; system prompt injected here.
        `user_type` - persona overlay; None -> generic (asks a clarifying question).
        `context` - trusted frontend data, appended to the system prompt as
        authoritative numbers so the model needn't re-verify via tools.
        `trace` - per-request debug trace; disabled/omitted = silent.
        """
        trace = trace or DebugTrace(enabled=self.settings.ai_debug_log)
        if not self.settings.dashscope_api_key.get_secret_value():
            result = AIResult(
                reply=REFUSAL_MESSAGE,
                blocked=True,
                block_reason="dashscope_api_key_not_configured",
            )
            trace.request_out(result.reply, 0, True, result.block_reason)
            return result

        truncated = ai_history.truncate_messages(
            messages,
            window=self.settings.ai_history_window,
            max_tokens=self.settings.ai_history_max_tokens,
        )
        scrubbed = ai_safety.scrub_messages(truncated)

        system_prompt = get_system_prompt(mode, user_type) + format_context(context)
        convo: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        convo.extend(scrubbed)

        result = self._run_tool_loop(conn, convo, trace)

        # deterministic output filter
        verdict = ai_safety.check_output(result.reply)
        if not verdict.safe:
            logger.warning("Deterministic filter blocked output: %s", verdict.reason)
            result = AIResult(
                reply=REFUSAL_MESSAGE,
                tool_calls=result.tool_calls,
                iterations=result.iterations,
                blocked=True,
                block_reason=f"filter:{verdict.reason}",
            )
            trace.request_out(result.reply, result.iterations, True, result.block_reason)
            return result

        # optional self-critique pass
        if self.settings.ai_enable_self_critique:
            critique_verdict = self._self_critique(result.reply, trace)
            if not critique_verdict.startswith("SAFE"):
                logger.warning("Self-critique blocked output: %s", critique_verdict)
                result = AIResult(
                    reply=REFUSAL_MESSAGE,
                    tool_calls=result.tool_calls,
                    iterations=result.iterations,
                    blocked=True,
                    block_reason=f"critique:{critique_verdict[:80]}",
                )
                trace.request_out(result.reply, result.iterations, True, result.block_reason)
                return result

        trace.request_out(result.reply, result.iterations, result.blocked, result.block_reason)
        return result

    # --- Internals ----------------------------------------------------------

    def _run_tool_loop(
        self,
        conn: Connection,
        convo: list[dict[str, Any]],
        trace: DebugTrace,
    ) -> AIResult:
        """Run the LLM <-> tools loop until we get plain text back."""
        max_iter = self.settings.ai_max_tool_iterations
        total_budget = self.settings.ai_total_timeout_seconds
        started = time.monotonic()
        traces: list[ToolTrace] = []

        for iteration in range(1, max_iter + 1):
            # budget already burnt? bail with a clean refusal before nginx 504s us
            if time.monotonic() - started > total_budget:
                logger.warning(
                    "AI request exceeded total budget (%ss) at iteration %d",
                    total_budget,
                    iteration,
                )
                return AIResult(
                    reply=REFUSAL_MESSAGE,
                    tool_calls=traces,
                    iterations=iteration - 1,
                    blocked=True,
                    block_reason="request_timeout",
                )
            with trace.llm_call(self.settings.qwen_model, len(convo)) as span:
                # snapshot before sending - convo mutates next iteration
                span.capture_request(convo)
                try:
                    completion = self.client.chat.completions.create(
                        model=self.settings.qwen_model,
                        messages=convo,
                        tools=OPENAI_TOOLS,
                        tool_choice="auto",
                        max_tokens=self.settings.ai_max_tokens_per_request,
                        temperature=0.2,
                    )
                except APIError:
                    logger.exception("DashScope API call failed")
                    return AIResult(
                        reply=REFUSAL_MESSAGE,
                        tool_calls=traces,
                        iterations=iteration,
                        blocked=True,
                        block_reason="upstream_api_error",
                    )

            choice = completion.choices[0]
            msg = choice.message
            finish_reason = choice.finish_reason
            span.capture_response(msg.content, getattr(msg, "tool_calls", None) or [])
            span.finish(
                finish_reason,
                len(msg.content or ""),
                len(getattr(msg, "tool_calls", None) or []),
            )

            # model wants to call tools
            tool_calls = getattr(msg, "tool_calls", None) or []
            if tool_calls:
                # keep content as None (not "") when tool_calls present -
                # per the OpenAI spec, some validators are strict about it
                convo.append(
                    {
                        "role": "assistant",
                        "content": msg.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in tool_calls
                        ],
                    }
                )

                for tc in tool_calls:
                    name = tc.function.name
                    arguments = tc.function.arguments or "{}"
                    result_json = dispatch_tool(conn, name, arguments)
                    ok = '"error"' not in result_json
                    trace.tool_call(name, arguments, ok, result_json)
                    traces.append(ToolTrace(name=name, arguments=arguments, ok=ok))
                    convo.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result_json,
                        }
                    )
                continue  # loop back so the model reads the results

            # no tool call -> final assistant text
            reply = (msg.content or "").strip()
            if not reply or finish_reason == "length":
                # `length` = hit max_tokens, treat content as untrusted
                return AIResult(
                    reply=REFUSAL_MESSAGE,
                    tool_calls=traces,
                    iterations=iteration,
                    blocked=True,
                    block_reason="empty_or_truncated",
                )
            return AIResult(reply=reply, tool_calls=traces, iterations=iteration)

        # hit the iteration cap with no final answer
        logger.warning("AI tool loop exhausted %d iterations", max_iter)
        return AIResult(
            reply=REFUSAL_MESSAGE,
            tool_calls=traces,
            iterations=max_iter,
            blocked=True,
            block_reason="tool_loop_exhausted",
        )

    def _self_critique(self, answer: str, trace: DebugTrace) -> str:
        """Second pass: same model judges the first. Returns the verdict line
        ("SAFE" / "BLOCKED: ..."). API failure -> "SAFE" so an upstream outage
        doesn't block every reply."""
        critique_messages = [
            {"role": "system", "content": SELF_CRITIQUE_PROMPT},
            {"role": "user", "content": answer},
        ]
        with trace.llm_call(self.settings.qwen_model + " (self-critique)", 2) as span:
            span.capture_request(critique_messages)
            try:
                completion = self.client.chat.completions.create(
                    model=self.settings.qwen_model,
                    messages=critique_messages,
                    max_tokens=64,
                    temperature=0.0,
                )
                msg = completion.choices[0].message
                span.capture_response(msg.content, [])
                verdict = (msg.content or "").strip()
                return verdict or "SAFE"
            except APIError:
                logger.exception("Self-critique call failed; treating answer as SAFE")
                return "SAFE"


# --- FastAPI integration helpers --------------------------------------------


_singleton: AIService | None = None


def get_ai_service() -> AIService:
    """Lazy singleton, lives as long as the app process."""
    global _singleton
    if _singleton is None:
        _singleton = AIService()
    return _singleton
