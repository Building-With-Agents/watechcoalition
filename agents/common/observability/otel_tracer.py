"""
OTelTracer — OpenTelemetry concrete tracer implementation.
EXP-006 candidate: vendor-neutral distributed tracing standard.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Generator

from agents.common.tracer_base import TracerBase

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


class OTelTracer(TracerBase):
    """Tracer that emits OpenTelemetry spans."""

    def __init__(self, agent_id: str = "unknown-agent") -> None:
        self._agent_id = agent_id
        self._spans: list[dict[str, Any]] = []
        if _OTEL_AVAILABLE:
            provider = TracerProvider()
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(agent_id)
        else:
            self._tracer = None

    @contextmanager
    def start_span(
        self,
        name: str,
        *,
        correlation_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[Any, None, None]:
        start = time.perf_counter()
        span_record: dict[str, Any] = {
            "name": name,
            "correlation_id": correlation_id,
            "agent_id": self._agent_id,
            "metadata": metadata or {},
            "status": "running",
            "events": [],
        }
        self._spans.append(span_record)
        try:
            yield None
            elapsed = time.perf_counter() - start
            span_record["status"] = "success"
            span_record["duration_seconds"] = round(elapsed, 4)
        except Exception as exc:
            elapsed = time.perf_counter() - start
            span_record["status"] = "error"
            span_record["duration_seconds"] = round(elapsed, 4)
            span_record["error"] = str(exc)
            raise

    def log_event(self, event_name: str, payload: dict[str, Any], *, level: str = "info") -> None:
        if self._spans:
            self._spans[-1]["events"].append({"event": event_name, "level": level, **payload})

    def record_latency(self, operation: str, *, seconds: float) -> None:
        self.log_event("latency", {"operation": operation, "seconds": round(seconds, 4)})

    def increment_counter(self, metric: str, *, value: int = 1) -> None:
        self.log_event("counter", {"metric": metric, "value": value})

    def record_error(self, error: Exception, *, context: dict[str, Any] | None = None) -> None:
        if self._spans:
            self._spans[-1]["events"].append({"event": "error_recorded", "error": str(error), "error_type": type(error).__name__, **(context or {})})
            self._spans[-1]["status"] = "error"

    def get_spans(self) -> list[dict[str, Any]]:
        return self._spans

    def clear_spans(self) -> None:
        self._spans.clear()
