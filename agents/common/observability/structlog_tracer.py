"""
StructlogTracer — structlog-only concrete tracer implementation.
EXP-006 candidate: baseline structured logging, zero setup.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Generator

import structlog

from agents.common.tracer_base import TracerBase


class StructlogTracer(TracerBase):
    """Tracer that writes every trace event as a structured log line via structlog."""

    def __init__(self, agent_id: str = "unknown-agent") -> None:
        self._agent_id = agent_id
        self._log = structlog.get_logger().bind(agent_id=agent_id, tracer="structlog")

    @contextmanager
    def start_span(
        self,
        name: str,
        *,
        correlation_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        span_log = self._log.bind(span=name, correlation_id=correlation_id, **(metadata or {}))
        start = time.perf_counter()
        span_log.info("span_started")
        try:
            yield None
            elapsed = time.perf_counter() - start
            span_log.info("span_finished", duration_seconds=round(elapsed, 4))
        except Exception as exc:
            elapsed = time.perf_counter() - start
            span_log.error("span_error", duration_seconds=round(elapsed, 4), error=str(exc), error_type=type(exc).__name__)
            raise

    def log_event(self, event_name: str, payload: dict[str, Any], *, level: str = "info") -> None:
        log_fn = getattr(self._log, level, self._log.info)
        log_fn(event_name, **payload)

    def record_latency(self, operation: str, *, seconds: float) -> None:
        self._log.info("latency", operation=operation, seconds=round(seconds, 4))

    def increment_counter(self, metric: str, *, value: int = 1) -> None:
        self._log.info("counter", metric=metric, value=value)

    def record_error(self, error: Exception, *, context: dict[str, Any] | None = None) -> None:
        self._log.error("error_recorded", error=str(error), error_type=type(error).__name__, **(context or {}))
