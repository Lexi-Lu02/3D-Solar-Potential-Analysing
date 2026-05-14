"""
Server-side conversation-history truncation.

The frontend persists the full conversation in localStorage and sends it back
on every request (`messages: [{role, content}, ...]`). The backend is
stateless: this module's job is to take that array and trim it to fit inside
the model's effective context budget before we add the system prompt and the
tool-loop bookkeeping.

Design:
  1. Drop everything older than the last N messages (configurable).
  2. While the rough token estimate of the remaining messages exceeds the
     configured budget, drop one more from the front.
  3. Repair the head so the kept window is well-formed
     (user -> assistant -> user -> ... -> user).
"""

from __future__ import annotations

from typing import Iterable

# Rough char-per-token figures. Chinese is denser, English is sparser.
# We use a conservative blended rate and add a small overhead per message
# for role/JSON framing. Better than nothing without pulling in tiktoken.
_CHARS_PER_TOKEN_CN = 1.5
_CHARS_PER_TOKEN_EN = 4.0
_PER_MESSAGE_OVERHEAD_TOKENS = 4


def estimate_tokens(text: str) -> int:
    """Rough token estimate; biased slightly high to be safe."""
    if not text:
        return 0
    # Count CJK code points; treat the rest as English-ish.
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
    Trim `messages` to fit `window` items AND `max_tokens` rough budget.

    The last message (the user's current question) is always preserved.
    Returns a new list; does not mutate the input.
    """
    if not messages:
        return []

    # Always keep the tail (current question + recent context).
    kept = messages[-window:] if window > 0 else list(messages)

    # If even the head-most message of the window is now an orphan assistant,
    # drop it before checking budget. The model expects the first non-system
    # message to be `user`.
    kept = _repair_head(kept)

    # Token-budget pass: drop from the front until we fit, but never drop
    # the final user message (the current question).
    while len(kept) > 1 and _messages_token_estimate(kept) > max_tokens:
        kept.pop(0)
        kept = _repair_head(kept)

    # Last-resort safety: if a single message blows the budget on its own,
    # truncate its content. Better a clipped question than a 413.
    if kept and _messages_token_estimate(kept) > max_tokens:
        last = dict(kept[-1])
        budget_chars = max(200, max_tokens * 2)  # crude reverse of the estimate
        content = last.get("content") or ""
        if len(content) > budget_chars:
            last["content"] = content[:budget_chars] + "\n... [truncated]"
            kept[-1] = last

    return kept


def _repair_head(messages: list[dict]) -> list[dict]:
    """
    Drop leading messages until the first one has role 'user', so the kept
    window is well-formed for the chat completions API.
    """
    out = list(messages)
    while out and out[0].get("role") != "user":
        out.pop(0)
    return out


def summarize_dropped(_dropped: list[dict]) -> str | None:
    """
    Placeholder for an LLM-based summary of conversation chunks that were
    truncated. Iteration 3 does not implement this; iterate later if users
    complain about lost context.
    """
    return None
