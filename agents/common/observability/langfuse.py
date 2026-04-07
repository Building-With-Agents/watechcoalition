"""
LangfuseTracer — Langfuse concrete tracer implementation.

Sends real traces to Langfuse Cloud (or self-hosted) via the Langfuse Python SDK v4.
Also maintains in-memory trace records for test assertions (get_traces/clear_traces).
Env vars: LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_BASE_URL.
"""

from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from agents.common.tracer_base import TracerBase

try:
    from langfuse import Langfuse

    _LANGFUSE_AVAILABLE = True
except ImportError:
    _LANGFUSE_AVAILABLE = False


class LangfuseTracer(TracerBase):
    """Tracer that sends spans and events to Langfuse.

    Uses an observation stack so nested spans (e.g., enrichment wrapping
    LLM call generations) correctly maintain parent references for
    log_event, record_latency, etc.

    Also records trace data in-memory for test assertions via
    get_traces() / clear_traces().
    """

    def __init__(self, agent_id: str = "unknown-agent") -> None:
        self._agent_id = agent_id
        self._client = Langfuse() if _LANGFUSE_AVAILABLE else None
        self._observation_stack: list[Any] = []
        self._traces: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Parent trace (wraps an entire processing iteration)
    # ------------------------------------------------------------------

    @contextmanager
    def start_trace(
        self,
        name: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        """Create a parent span that wraps an entire processing iteration.

        All start_span() calls within this context become child observations
        via Langfuse SDK's context propagation.
        """
        if not self._client:
            yield None
            return

        trace_metadata = {"agent_id": self._agent_id, **(metadata or {})}
        try:
            with self._client.start_as_current_observation(
                name=name,
                as_type="span",
                metadata=trace_metadata,
            ) as trace_obs:
                self._observation_stack.append(trace_obs)
                try:
                    yield None
                finally:
                    self._observation_stack.pop()
        finally:
            try:
                self._client.flush()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Span (one generation / LLM call)
    # ------------------------------------------------------------------

    @contextmanager
    def start_span(
        self,
        name: str,
        *,
        correlation_id: str,
        input: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        span_metadata = {
            "agent_id": self._agent_id,
            **(metadata or {}),
        }

        # In-memory trace record (for test assertions)
        start = time.perf_counter()
        trace_record: dict[str, Any] = {
            "name": name,
            "correlation_id": correlation_id,
            "agent_id": self._agent_id,
            "metadata": span_metadata,
            "status": "running",
            "events": [],
        }
        self._traces.append(trace_record)

        if not self._client:
            try:
                yield None
                trace_record["status"] = "success"
                trace_record["duration_seconds"] = round(time.perf_counter() - start, 4)
            except Exception as exc:
                trace_record["status"] = "error"
                trace_record["error"] = str(exc)
                trace_record["duration_seconds"] = round(time.perf_counter() - start, 4)
                raise
            return

        try:
            with self._client.start_as_current_observation(
                name=f"{self._agent_id}/{name}",
                as_type="generation",
                model=span_metadata.get("model"),
                input=input,
                metadata=span_metadata,
            ) as observation:
                self._observation_stack.append(observation)
                try:
                    yield None
                    trace_record["status"] = "success"
                    trace_record["duration_seconds"] = round(time.perf_counter() - start, 4)
                except Exception as exc:
                    observation.update(
                        level="ERROR",
                        status_message=str(exc),
                    )
                    trace_record["status"] = "error"
                    trace_record["error"] = str(exc)
                    trace_record["duration_seconds"] = round(time.perf_counter() - start, 4)
                    raise
                finally:
                    self._observation_stack.pop()
        finally:
            # Flush to ensure trace is sent (non-blocking batch flush)
            try:
                self._client.flush()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Event logging
    # ------------------------------------------------------------------

    def log_event(self, event_name: str, payload: dict[str, Any], *, level: str = "info") -> None:
        # Record in-memory for test assertions
        if self._traces:
            self._traces[-1]["events"].append(
                {"event": event_name, "level": level, **payload}
            )

        obs = self._observation_stack[-1] if self._observation_stack else None
        if obs is None:
            return
        try:
            update_kwargs: dict[str, Any] = {}
            if "input_tokens" in payload and "output_tokens" in payload:
                update_kwargs["usage_details"] = {
                    "input": payload["input_tokens"],
                    "output": payload["output_tokens"],
                    "total": payload["input_tokens"] + payload["output_tokens"],
                }
            if "cost_usd" in payload:
                update_kwargs["cost_details"] = {"total": payload["cost_usd"]}
            if "output" in payload:
                update_kwargs["output"] = payload["output"]
            if update_kwargs:
                obs.update(**update_kwargs)
        except Exception:
            pass

    def record_latency(self, operation: str, *, seconds: float) -> None:
        # Record in-memory for test assertions
        if self._traces:
            self._traces[-1]["events"].append(
                {"event": "latency", "operation": operation, "seconds": round(seconds, 4)}
            )

        obs = self._observation_stack[-1] if self._observation_stack else None
        if obs is None:
            return
        try:
            obs.update(metadata={"latency_seconds": round(seconds, 4)})
        except Exception:
            pass

    def increment_counter(self, metric: str, *, value: int = 1) -> None:
        # Record in-memory for test assertions
        if self._traces:
            self._traces[-1]["events"].append(
                {"event": "counter", "metric": metric, "value": value}
            )

        obs = self._observation_stack[-1] if self._observation_stack else None
        if obs is None:
            return
        try:
            obs.update(metadata={f"counter_{metric}": value})
        except Exception:
            pass

    def record_error(self, error: Exception, *, context: dict[str, Any] | None = None) -> None:
        # Record in-memory for test assertions
        if self._traces:
            self._traces[-1]["events"].append(
                {"event": "error_recorded", "error": str(error),
                 "error_type": type(error).__name__, **(context or {})}
            )
            self._traces[-1]["status"] = "error"

        obs = self._observation_stack[-1] if self._observation_stack else None
        if obs is None:
            return
        try:
            obs.update(
                level="ERROR",
                status_message=f"{type(error).__name__}: {error}",
                metadata={"error_context": context or {}},
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        """Flush pending traces and release resources."""
        if self._client:
            try:
                self._client.flush()
                self._client.shutdown()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Test helpers (in-memory trace recording)
    # ------------------------------------------------------------------

    def get_traces(self) -> list[dict[str, Any]]:
        """Return in-memory trace records for test assertions."""
        return self._traces

    def clear_traces(self) -> None:
        """Clear in-memory trace records."""
        self._traces.clear()
