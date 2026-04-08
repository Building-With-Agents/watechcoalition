"""Shared async retry/backoff helpers for Pass 2 LLM extractors.

All three async extractors (tasks, responsibilities, skills) use the same
two-level retry strategy:

1. Timeout retry: one additional attempt on ``TimeoutError`` after a short sleep.
2. Rate-limit backoff: exponential waits when Azure returns 429, with jitter
   to avoid thundering herd under high concurrency.
"""

from __future__ import annotations

from typing import Any

# Back-off delays for 429 in seconds. Azure OpenAI typically asks for 10-30s.
# Jitter added at runtime to prevent thundering herd.
RATE_LIMIT_BACKOFF_SECS: tuple[int, ...] = (5, 15, 30, 60)
RATE_LIMIT_MAX_CYCLES: int = 4


def is_rate_limited(meta: dict[str, Any]) -> bool:
    """Return True when LLM metadata indicates a 429 rate-limit response."""
    return not meta.get("success") and (
        meta.get("is_rate_limit")
        or meta.get("retry_after_seconds") is not None
        or "429" in str(meta.get("error_reason", ""))
    )


def merge_retry_metadata(metadata: dict[str, Any], meta: dict[str, Any]) -> None:
    """Accumulate token/cost/latency across retry attempts, keeping latest labels."""
    metadata["tokens_used"] = metadata.get("tokens_used", 0) + meta.get("tokens_used", 0)
    metadata["cost_usd"] = metadata.get("cost_usd", 0.0) + meta.get("cost_usd", 0.0)
    metadata["latency_ms"] = metadata.get("latency_ms", 0) + meta.get("latency_ms", 0)
    metadata["provider"] = meta.get("provider", metadata.get("provider", ""))
    metadata["model"] = meta.get("model", metadata.get("model", ""))
