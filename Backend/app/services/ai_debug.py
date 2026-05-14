"""
Verbose request/response tracing for the AI pipeline.

Two consumers, one source of truth:

1. **Console log**  - when `AI_DEBUG_LOG=true`, every event is written to the
   standard logger so you can `tail -f` uvicorn's terminal.

2. **In-memory ring buffer**  - every event is also appended to a
   `TraceRecord` held by `recorder`. The `/api/v1/ai/debug/ui` page reads
   the buffer and renders a per-request timeline. Survives until process
   restart; capped at `MAX_RECORDS` to bound memory.

Both consumers are populated by the same `DebugTrace` object that flows
through the AI service. When console logging is off, recording still runs
(it's cheap), so the UI works regardless of the console-log setting.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

logger = logging.getLogger("app.ai.debug")

_SEP = "=" * 70
_SUB = "-" * 70
_PREVIEW_CHARS = 600
MAX_RECORDS = 50


# ---------------------------------------------------------------------------
# Structured records (consumed by the UI page)
# ---------------------------------------------------------------------------


@dataclass
class LLMCallRecord:
    n: int
    model: str
    msg_count: int
    started_at: float
    elapsed_s: float | None = None
    finish_reason: str | None = None
    content_chars: int = 0
    tool_call_count: int = 0
    failed: bool = False
    # Raw payload sent to Qwen + raw response received. Captured so the UI can
    # show *exactly* what was on the wire, not just a summary. Stored as
    # plain dicts (deep-ish copy) so later mutation of `convo` doesn't leak in.
    request_messages: list[dict] = field(default_factory=list)
    response_content: str | None = None
    response_tool_calls: list[dict] = field(default_factory=list)


@dataclass
class ToolCallRecord:
    n: int
    name: str
    arguments: str
    ok: bool
    result_preview: str


@dataclass
class TraceRecord:
    id: str
    started_at: float            # epoch seconds
    endpoint: str = ""
    mode: str = ""
    user_type: str | None = None
    messages: list[dict] = field(default_factory=list)
    llm_calls: list[LLMCallRecord] = field(default_factory=list)
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    reply: str = ""
    iterations: int = 0
    blocked: bool = False
    block_reason: str | None = None
    total_elapsed_s: float | None = None
    finished: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "started_at": self.started_at,
            "endpoint": self.endpoint,
            "mode": self.mode,
            "user_type": self.user_type,
            "messages": self.messages,
            "llm_calls": [c.__dict__ for c in self.llm_calls],
            "tool_calls": [c.__dict__ for c in self.tool_calls],
            "reply": self.reply,
            "iterations": self.iterations,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "total_elapsed_s": self.total_elapsed_s,
            "finished": self.finished,
        }


class TraceRecorder:
    """Thread-safe ring buffer of recent TraceRecords."""

    def __init__(self, max_records: int = MAX_RECORDS):
        self._lock = threading.Lock()
        self._records: deque[TraceRecord] = deque(maxlen=max_records)

    def add(self, record: TraceRecord) -> None:
        with self._lock:
            self._records.append(record)

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            # Newest first.
            return [r.to_dict() for r in reversed(self._records)]

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


recorder = TraceRecorder()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _safe_copy_message(m: dict) -> dict:
    """Shallow-copy a chat message into a JSON-safe plain dict.

    Tool-call dicts inside an assistant message are nested-copied because
    the caller may rebuild the list later (we don't want the snapshot to
    follow those mutations).
    """
    out: dict[str, Any] = {"role": m.get("role"), "content": m.get("content")}
    if "tool_call_id" in m:
        out["tool_call_id"] = m["tool_call_id"]
    if "name" in m:
        out["name"] = m["name"]
    if "tool_calls" in m and m["tool_calls"]:
        out["tool_calls"] = [
            {
                "id": tc.get("id"),
                "type": tc.get("type", "function"),
                "function": {
                    "name": tc.get("function", {}).get("name"),
                    "arguments": tc.get("function", {}).get("arguments", ""),
                },
            }
            for tc in m["tool_calls"]
        ]
    return out


def _short(text: str | None, limit: int = _PREVIEW_CHARS) -> str:
    if text is None:
        return "<None>"
    s = str(text)
    if len(s) <= limit:
        return s
    return s[:limit] + f"... [+{len(s) - limit} chars]"


# ---------------------------------------------------------------------------
# DebugTrace: passed through the service layer; populates both log + record
# ---------------------------------------------------------------------------


class DebugTrace:
    """One request's debug trace.

    Created in the router, threaded into the service. Both the structured
    `TraceRecord` (for the UI) and console log lines come from here.

    `enabled` only controls *console logging*; structured recording always
    runs so the UI works even when terminal log is too noisy.
    """

    def __init__(self, enabled: bool, request_id: str | None = None):
        self.enabled = enabled
        self.id = request_id or uuid.uuid4().hex[:8]
        self.t0 = time.monotonic()
        self.record = TraceRecord(id=self.id, started_at=time.time())
        self._llm_calls = 0
        self._tool_calls = 0

    def _emit(self, lines: list[str]) -> None:
        if not self.enabled:
            return
        logger.info("\n" + "\n".join(lines))

    # --- request boundary ------------------------------------------------

    def request_in(
        self,
        endpoint: str,
        mode: str,
        user_type: str | None,
        messages: list[dict],
    ) -> None:
        self.record.endpoint = endpoint
        self.record.mode = mode
        self.record.user_type = user_type
        # Defensive copy so later mutations to the messages list don't leak in.
        self.record.messages = [
            {"role": m.get("role"), "content": m.get("content")} for m in messages
        ]

        lines = [
            _SEP,
            f"[AI:{self.id}] >>> {endpoint}  mode={mode}  user_type={user_type!r}",
            _SUB,
            f"messages ({len(messages)} total):",
        ]
        for i, m in enumerate(messages):
            role = m.get("role", "?")
            content = m.get("content")
            lines.append(f"  [{i}] {role}: {_short(content, 400)}")
        lines.append(_SEP)
        self._emit(lines)

    def request_out(
        self,
        reply: str,
        iterations: int,
        blocked: bool,
        block_reason: str | None,
    ) -> None:
        elapsed = time.monotonic() - self.t0
        self.record.reply = reply
        self.record.iterations = iterations
        self.record.blocked = blocked
        self.record.block_reason = block_reason
        self.record.total_elapsed_s = elapsed
        self.record.finished = True
        recorder.add(self.record)

        lines = [
            _SEP,
            f"[AI:{self.id}] <<< done in {elapsed:.2f}s  "
            f"llm_calls={self._llm_calls}  tool_calls={self._tool_calls}  "
            f"iterations={iterations}  blocked={blocked}",
        ]
        if blocked:
            lines.append(f"[AI:{self.id}]     block_reason: {block_reason}")
        lines.append(f"[AI:{self.id}]     reply ({len(reply)} chars):")
        for line in (_short(reply, 1500).splitlines() or [""]):
            lines.append(f"[AI:{self.id}]       {line}")
        lines.append(_SEP)
        self._emit(lines)

    # --- per-LLM-call span ----------------------------------------------

    def llm_call(self, model: str, msg_count: int) -> "_LLMCallSpan":
        self._llm_calls += 1
        rec = LLMCallRecord(
            n=self._llm_calls,
            model=model,
            msg_count=msg_count,
            started_at=time.time(),
        )
        self.record.llm_calls.append(rec)
        return _LLMCallSpan(self, rec)

    # --- per-tool-call ---------------------------------------------------

    def tool_call(self, name: str, arguments: str, ok: bool, result_json: str) -> None:
        self._tool_calls += 1
        try:
            preview = json.dumps(json.loads(result_json), ensure_ascii=False)[:_PREVIEW_CHARS]
        except (TypeError, ValueError):
            preview = _short(result_json)

        self.record.tool_calls.append(
            ToolCallRecord(
                n=self._tool_calls,
                name=name,
                arguments=arguments,
                ok=ok,
                result_preview=preview,
            )
        )

        lines = [
            f"[AI:{self.id}]   tool#{self._tool_calls} {'OK ' if ok else 'ERR'} {name}",
            f"[AI:{self.id}]     args:   {_short(arguments, 300)}",
            f"[AI:{self.id}]     result: {preview}",
        ]
        self._emit(lines)


class _LLMCallSpan:
    """Context-manager that times one upstream Qwen call."""

    def __init__(self, parent: DebugTrace, record: LLMCallRecord):
        self.parent = parent
        self.record = record
        self.t0 = 0.0

    def __enter__(self) -> "_LLMCallSpan":
        self.t0 = time.monotonic()
        if self.parent.enabled:
            logger.info(
                f"[AI:{self.parent.id}]   llm#{self.record.n} -> POST {self.record.model}  "
                f"({self.record.msg_count} msgs in convo)"
            )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        elapsed = time.monotonic() - self.t0
        self.record.elapsed_s = elapsed
        if exc_type is not None:
            self.record.failed = True
        if not self.parent.enabled:
            return
        if exc_type is None:
            logger.info(f"[AI:{self.parent.id}]   llm#{self.record.n} <- {elapsed:.2f}s")
        else:
            logger.info(
                f"[AI:{self.parent.id}]   llm#{self.record.n} <- {elapsed:.2f}s "
                f"FAILED ({exc_type.__name__})"
            )

    def capture_request(self, messages: list[dict]) -> None:
        """Snapshot the messages array right before the SDK call goes out."""
        # Defensive copy: convo is mutated after the call (we append assistant
        # + tool messages), so we need a snapshot, not a reference.
        snapshot: list[dict] = []
        for m in messages:
            snapshot.append(_safe_copy_message(m))
        self.record.request_messages = snapshot

    def capture_response(
        self, content: str | None, tool_calls: list[Any]
    ) -> None:
        """Snapshot what the model actually replied with."""
        self.record.response_content = content
        self.record.response_tool_calls = [
            {
                "id": getattr(tc, "id", None),
                "type": getattr(tc, "type", "function"),
                "function": {
                    "name": getattr(tc.function, "name", "?"),
                    "arguments": getattr(tc.function, "arguments", ""),
                },
            }
            for tc in (tool_calls or [])
            if hasattr(tc, "function")
        ]

    def finish(self, finish_reason: str | None, content_chars: int, tool_calls: int) -> None:
        self.record.finish_reason = finish_reason
        self.record.content_chars = content_chars
        self.record.tool_call_count = tool_calls
        if not self.parent.enabled:
            return
        logger.info(
            f"[AI:{self.parent.id}]   llm#{self.record.n}    finish_reason={finish_reason!r}  "
            f"content_chars={content_chars}  tool_calls={tool_calls}"
        )


@contextmanager
def noop_trace() -> Iterator[DebugTrace]:
    """When recording is undesired, hand out a disabled trace that doesn't record."""
    yield DebugTrace(enabled=False)
