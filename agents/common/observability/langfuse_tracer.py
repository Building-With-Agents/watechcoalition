"""
LangfuseTracer — Langfuse concrete tracer implementation.
EXP-006 candidate: open-source LLM observability, hosted or self-hosted.
"""

from __future__ import annotations

import time
import uuid
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
    """Tracer that sends spans and events to Langfuse."""

    def __init__(self, agent_id: str = "unknown-agent") -> None:
        self._agent_id = agent_id
        self._client = Langfuse() if _LANGFUSE_AVAILABLE else None
        self._traces: list[dict[str, Any]] = []
        self._active_trace_id: str | None = None

    @contextmanager
    def start_span(
        self,
        name: str,
        *,
        correlation_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        span_id = str(uuid.uuid4())
        start = time.perf_counter()
        trace_record: dict[str, Any] = {
            "span_id": span_id,
            "name": name,
            "correlation_id": correlation_id,
            "agent_id": self._agent_id,
            "metadata": metadata or {},
            "status": "running",
            "events": [],
        }
        self._traces.append(trace_record)
        self._active_trace_id = span_id
        try:
            yield None
            elapsed = time.perf_counter() - start
            trace_record["status"] = "success"
            trace_record["duration_seconds"] = round(elapsed, 4)
        except Exception as exc:
            elapsed = time.perf_counter() - start
            trace_record["status"] = "error"
            trace_record["duration_seconds"] = round(elapsed, 4)
            trace_record["error"] = str(exc)
            raise
        finally:
            self._active_trace_id = None

    def log_event(self, event_name: str, payload: dict[str, Any], *, level: str = "info") -> None:
        active = self._get_active_trace()
        if active is not None:
            active["events"].append({"event": event_name, "level": level, **payload})

    def record_latency(self, operation: str, *, seconds: float) -> None:
        self.log_event("latency", {"operation": operation, "seconds": round(seconds, 4)})

    def increment_counter(self, metric: str, *, value: int = 1) -> None:
        self.log_event("counter", {"metric": metric, "value": value})

    def record_error(self, error: Exception, *, context: dict[str, Any] | None = None) -> None:
        active = self._get_active_trace()
        if active is not None:
            active["events"].append({"event": "error_recorded", "error": str(error), "error_type": type(error).__name__, **(context or {})})
            active["status"] = "error"

    def _get_active_trace(self) -> dict[str, Any] | None:
        if self._active_trace_id is None:
            return None
        for t in reversed(self._traces):
            if t["span_id"] == self._active_trace_id:
                return t
        return None

    def get_traces(self) -> list[dict[str, Any]]:
        return self._traces

    def clear_traces(self) -> None:
        self._traces.clear()
        self._active_trace_id = None
