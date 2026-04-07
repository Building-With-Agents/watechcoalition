"""Centralized LLM adapter for all agents.

Every LLM call in the pipeline flows through here. Handles:
- Making the actual API call
- Timing and token tracking
- Cost computation
- Logging every call to llm_audit_log via log_extraction_event()
- Retry once on timeout, then return extraction_failed=True
- Exponential back-off on 429 (1s → 2s → 4s → 8s); queue is implicit (caller holds batch)
- SkillsExtractionAlert event emitted after 3 back-off cycles (if bus registered)
- Optional Langfuse tracing via register_tracer()

All LLM calls from any agent must flow through this adapter — no per-agent logging.
Uses structlog only. No credentials in code — env vars only.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import time
import uuid
from contextlib import nullcontext
from typing import Any

import structlog

from agents.common.data_store.database import session_scope
from agents.common.data_store.models import LLMAuditLog
from agents.common.observability.langfuse import LangfuseTracer

log = structlog.get_logger()

# Optional bus for emitting SkillsExtractionAlert; set via register_alert_bus()
_alert_bus: Any = None

# Optional Langfuse tracer; set via register_tracer() so every LLM call can be traced
_tracer: LangfuseTracer | None = None


def get_tracer() -> LangfuseTracer | None:
    """Return the currently registered tracer (None if not set)."""
    return _tracer

# ---------------------------------------------------------------------------
# Pricing (per token) — configurable via env vars
# ---------------------------------------------------------------------------

PRICING = {
    "sonnet": {
        "input": float(os.getenv("SONNET_INPUT_COST_PER_TOKEN", str(3.00 / 1_000_000))),
        "output": float(os.getenv("SONNET_OUTPUT_COST_PER_TOKEN", str(15.00 / 1_000_000))),
    },
    "haiku": {
        "input": float(os.getenv("HAIKU_INPUT_COST_PER_TOKEN", str(0.25 / 1_000_000))),
        "output": float(os.getenv("HAIKU_OUTPUT_COST_PER_TOKEN", str(1.25 / 1_000_000))),
    },
}

# Model name → tier mapping
MODEL_TIER_MAP = {
    "claude-sonnet-4-5": "sonnet",
    "claude-haiku-4-5": "haiku",
}

# Back-off settings
_BACKOFF_SEQUENCE = [1, 2, 4, 8]
_ALERT_AFTER_CYCLES = 3


# ---------------------------------------------------------------------------
# Cost computation
# ---------------------------------------------------------------------------


def compute_extraction_cost(input_tokens: int, output_tokens: int, model_tier: str) -> float:
    """Return cost in USD for a given token count and model tier."""
    tier = PRICING.get(model_tier)
    if not tier:
        log.warning("unknown_model_tier", model_tier=model_tier)
        return 0.0
    return (input_tokens * tier["input"]) + (output_tokens * tier["output"])


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------


def log_extraction_event(
    agent_name: str,
    prompt: str,
    model: str,
    provider: str,
    latency_ms: int,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    success: bool,
    error_reason: str | None = None,
) -> None:
    """Centralized logging: write one row to llm_audit_log after every LLM call.

    Never raises — logging must not break the pipeline. All agents use this
    via the adapter; no per-agent logging.
    """
    try:
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        with session_scope() as session:
            session.add(
                LLMAuditLog(
                    agent_name=agent_name,
                    prompt_hash=prompt_hash,
                    model=model,
                    provider=provider,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    token_count=input_tokens + output_tokens,
                    cost_usd=cost_usd,
                    success=success,
                    error_reason=error_reason,
                )
            )
    except Exception as exc:
        log.warning("llm_audit_log_write_failed", error=str(exc))


def handle_extraction_failure(
    agent_name: str,
    model_tier: str,
    error_reason: str,
    latency_ms: int = 0,
) -> dict[str, Any]:
    """Return standard failure result after timeout retry or other error.

    Retry-on-timeout is applied in complete() (once); then this result is returned
    with extraction_failed=True.
    """
    return {
        "content": "",
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "model_tier": model_tier,
        "success": False,
        "extraction_failed": True,
        "latency_ms": latency_ms,
        "error_reason": error_reason,
    }


# ---------------------------------------------------------------------------
# Main adapter
# ---------------------------------------------------------------------------


def complete(
    prompt: str,
    agent_name: str,
    model: str | None = None,
    system: str | None = None,
    max_tokens: int = 1000,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Make an LLM call, log it via log_extraction_event(), and return the result.

    Retries once on timeout; on second timeout or other API error returns
    via handle_extraction_failure() with extraction_failed=True.

    If a tracer is registered via register_tracer(), the call is wrapped in a
    Langfuse span; correlation_id is passed through when provided, else a new uuid.

    Returns a dict with:
        - content: str
        - input_tokens: int
        - output_tokens: int
        - cost_usd: float
        - model_tier: str
        - success: bool
        - extraction_failed: bool (True after timeout retry or API error)
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic")

    # Mock provider: return ground truth data, no API calls
    if provider == "mock":
        from agents.common.mock_llm_provider import mock_complete

        correlation_id = correlation_id or str(uuid.uuid4())
        span_ctx = (
            _tracer.start_span(agent_name, correlation_id=correlation_id, input=prompt,
                               metadata={"agent_name": agent_name, "model": "mock-sonnet-v1"})
            if _tracer
            else nullcontext()
        )
        with span_ctx:
            result = mock_complete(prompt, agent_name, model=model, system=system, max_tokens=max_tokens)
            log_extraction_event(
                agent_name=agent_name, prompt=prompt, model="mock-sonnet-v1",
                provider="mock", latency_ms=result.get("latency_ms", 0),
                input_tokens=result["input_tokens"], output_tokens=result["output_tokens"],
                cost_usd=result["cost_usd"], success=True,
            )
            if _tracer:
                try:
                    _tracer.log_event("llm_success", {
                        "input_tokens": result["input_tokens"],
                        "output_tokens": result["output_tokens"],
                        "cost_usd": result["cost_usd"],
                        "output": result["content"][:4000],
                    })
                except Exception:
                    pass
            return result

    try:
        from anthropic import Anthropic, APIStatusError, APITimeoutError
    except ImportError as exc:
        raise ImportError(
            "The 'anthropic' package is required when LLM_PROVIDER=anthropic. "
            "Install with: pip install anthropic\n"
            "If you are using Azure OpenAI, use agents.common.llm_client instead."
        ) from exc

    model = model or os.getenv("EXTRACTION_MODEL_SKILLS", "claude-sonnet-4-5")
    model_tier = MODEL_TIER_MAP.get(model, "sonnet")
    client = Anthropic()

    correlation_id = correlation_id or str(uuid.uuid4())
    span_metadata = {"agent_name": agent_name, "model": model, "model_tier": model_tier}
    span_ctx = (
        _tracer.start_span(agent_name, correlation_id=correlation_id, input=prompt, metadata=span_metadata)
        if _tracer
        else nullcontext()
    )

    messages = [{"role": "user", "content": prompt}]
    kwargs: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        kwargs["system"] = system

    backoff_cycles = 0

    with span_ctx:
        # --- Retry loop for rate limits ---
        while True:
            # --- Single attempt with one timeout retry ---
            for attempt in range(2):
                start = time.monotonic()
                try:
                    response = client.messages.create(**kwargs)
                    latency_ms = int((time.monotonic() - start) * 1000)

                    input_tokens = response.usage.input_tokens
                    output_tokens = response.usage.output_tokens
                    cost_usd = compute_extraction_cost(input_tokens, output_tokens, model_tier)
                    content = response.content[0].text

                    log_extraction_event(
                        agent_name=agent_name,
                        prompt=prompt,
                        model=model,
                        provider=provider,
                        latency_ms=latency_ms,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost_usd=cost_usd,
                        success=True,
                    )

                    log.info(
                        "llm_call_success",
                        agent=agent_name,
                        model=model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost_usd=round(cost_usd, 6),
                        latency_ms=latency_ms,
                    )

                    if _tracer:
                        try:
                            _tracer.record_latency("llm_call", seconds=latency_ms / 1000.0)
                            _tracer.log_event(
                                "llm_success",
                                {
                                    "input_tokens": input_tokens,
                                    "output_tokens": output_tokens,
                                    "cost_usd": round(cost_usd, 6),
                                    "output": content[:4000],
                                },
                            )
                        except Exception:
                            pass

                    return {
                        "content": content,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cost_usd": cost_usd,
                        "model_tier": model_tier,
                        "success": True,
                        "extraction_failed": False,
                    }

                except APITimeoutError as exc:
                    latency_ms = int((time.monotonic() - start) * 1000)
                    log.warning("llm_timeout", agent=agent_name, attempt=attempt + 1)
                    if attempt == 0:
                        continue  # retry once
                    # Both attempts timed out — log and return extraction_failed
                    log_extraction_event(
                        agent_name=agent_name,
                        prompt=prompt,
                        model=model,
                        provider=provider,
                        latency_ms=latency_ms,
                        input_tokens=0,
                        output_tokens=0,
                        cost_usd=0.0,
                        success=False,
                        error_reason=f"timeout: {exc}",
                    )
                    if _tracer:
                        with contextlib.suppress(Exception):
                            _tracer.record_error(exc, context={"agent_name": agent_name, "model": model})
                    return handle_extraction_failure(
                        agent_name=agent_name,
                        model_tier=model_tier,
                        error_reason=f"timeout: {exc}",
                        latency_ms=latency_ms,
                    )

                except APIStatusError as exc:
                    latency_ms = int((time.monotonic() - start) * 1000)
                    if exc.status_code == 429:
                        # Rate limit — break out of attempt loop, handle below
                        break
                    # Any other API error — log and return extraction_failed
                    log_extraction_event(
                        agent_name=agent_name,
                        prompt=prompt,
                        model=model,
                        provider=provider,
                        latency_ms=latency_ms,
                        input_tokens=0,
                        output_tokens=0,
                        cost_usd=0.0,
                        success=False,
                        error_reason=f"{exc.status_code}: {exc.message}",
                    )
                    if _tracer:
                        with contextlib.suppress(Exception):
                            _tracer.record_error(exc, context={"agent_name": agent_name, "model": model})
                    return handle_extraction_failure(
                        agent_name=agent_name,
                        model_tier=model_tier,
                        error_reason=f"{exc.status_code}: {exc.message}",
                        latency_ms=latency_ms,
                    )
                else:
                    break  # success — exit attempt loop

            else:
                # Only reached if attempt loop ended without a 429 break
                continue

            # --- Rate limit back-off ---
            backoff_cycles += 1
            wait = _BACKOFF_SEQUENCE[min(backoff_cycles - 1, len(_BACKOFF_SEQUENCE) - 1)]
            log.warning("llm_rate_limit_backoff", agent=agent_name, cycle=backoff_cycles, wait_s=wait)

            if backoff_cycles >= _ALERT_AFTER_CYCLES:
                _emit_skills_extraction_alert(agent_name, backoff_cycles)

            time.sleep(wait)


# ---------------------------------------------------------------------------
# Alert emission
# ---------------------------------------------------------------------------


def register_alert_bus(bus: Any) -> None:
    """Register the event bus so SkillsExtractionAlert can be published.

    Call once from the pipeline runner or orchestration layer. If not set,
    only structlog is used when the back-off threshold is exceeded.
    """
    global _alert_bus
    _alert_bus = bus


def register_tracer(tracer: LangfuseTracer | None) -> None:
    """Register a Langfuse tracer so every LLM call is automatically traced.

    Call once from the pipeline or orchestration layer. If not set, no
    tracing is performed; tracing is optional and must never break the pipeline.
    """
    global _tracer
    _tracer = tracer


def _emit_skills_extraction_alert(agent_name: str, backoff_cycles: int) -> None:
    """Emit SkillsExtractionAlert after 3+ rate limit back-off cycles.

    Logs via structlog always; publishes EventEnvelope if register_alert_bus()
    was called (Orchestration is the sole consumer).
    """
    log.error(
        "SkillsExtractionAlert",
        agent=agent_name,
        backoff_cycles=backoff_cycles,
        message="Rate limit back-off threshold exceeded. Pipeline may be degraded.",
    )
    if _alert_bus is None:
        return
    try:
        from agents.common.event_envelope import EventEnvelope

        event = EventEnvelope(
            correlation_id="",
            agent_id="skills-extraction-agent",
            payload={
                "event_type": "SkillsExtractionAlert",
                "agent_name": agent_name,
                "backoff_cycles": backoff_cycles,
                "message": "Rate limit back-off threshold exceeded. Pipeline may be degraded.",
            },
        )
        _alert_bus.publish(event)
    except Exception as exc:
        log.warning("SkillsExtractionAlert_publish_failed", error=str(exc))
