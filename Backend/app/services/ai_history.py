"""
Server-side conversation-history truncation.

Frontend sends back the whole transcript every request; this module trims it
to the model's context budget before we add the system prompt and tool-loop
bookkeeping.

Steps: keep the last N messages -> drop from the front while the token
estimate exceeds budget -> repair the head so the window starts with `user`.
"""

from __future__ import annotations

from typing import Iterable

# rough chars-per-token - Chinese denser, English sparser. plus a small
# per-message overhead for role/JSON framing. crude, but no tiktoken dep.
_CHARS_PER_TOKEN_CN = 1.5
_CHARS_PER_TOKEN_EN = 4.0
_PER_MESSAGE_OVERHEAD_TOKENS = 4


def estimate_tokens(text: str) -> int:
    """Rough token estimate, biased slightly high to be safe."""
    if not text:
        return 0
    # count CJK code points, treat the rest as English-ish
    cjk = sum(1 for ch in text if "一" <= ch <= "鿿")
    other = len(text) - cjk
    return int(cjk / _CHARS_PER_TOKEN_CN + other / _CHARS_PER_TOKEN_EN) + 1


def _messages_token_estimate(messages: Iterable[dict]) -> int:
    total = 0
    for m in messages:
        total += _PER_MESSAGE_OVERHEAD_TOKENS + estimate_tokens(m.get("content") or "")
    return total


def truncate_messages(
    messages: list[dict],
    *,
    window: int,
    max_tokens: int,
) -> list[dict]:
    """
    Trim `messages` to fit `window` items AND the `max_tokens` rough budget.

    The last message (current question) is always kept. Returns a new list,
    doesn't mutate the input.
    """
    if not messages:
        return []

    # keep the tail - current question + recent context
    kept = messages[-window:] if window > 0 else list(messages)

    # window head might now be an orphan assistant - first non-system msg
    # must be `user`
    kept = _repair_head(kept)

    # drop from the front until we fit, but never the final user message
    while len(kept) > 1 and _messages_token_estimate(kept) > max_tokens:
        kept.pop(0)
        kept = _repair_head(kept)

    # one message blows the budget alone? clip it - a clipped question beats a 413
    if kept and _messages_token_estimate(kept) > max_tokens:
        last = dict(kept[-1])
        budget_chars = max(200, max_tokens * 2)  # crude reverse of the estimate
        content = last.get("content") or ""
        if len(content) > budget_chars:
            last["content"] = content[:budget_chars] + "\n... [truncated]"
            kept[-1] = last

    return kept


def _repair_head(messages: list[dict]) -> list[dict]:
    """Drop leading messages until the first is role 'user' - keeps the
    window well-formed for the chat completions API."""
    out = list(messages)
    while out and out[0].get("role") != "user":
        out.pop(0)
    return out


def summarize_dropped(_dropped: list[dict]) -> str | None:
    """Placeholder - LLM summary of truncated chunks. Not implemented yet;
    add it later if users complain about lost context."""
    return None
