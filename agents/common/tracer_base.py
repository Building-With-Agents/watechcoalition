"""
TracerBase — Abstract Base Class for all observability/tracing implementations.

EXP-006: Each concrete tracer (structlog, LangSmith, Langfuse, OpenTelemetry)
implements this interface so the instrumented agent never couples to a specific
platform. Swap the tracer without touching agent code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


class TracerBase(ABC):
    """Abstract tracer that every concrete implementation must satisfy."""

    @contextmanager
    @abstractmethod
    def start_span(
        self,
        name: str,
        *,
        correlation_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[Any, None, None]:
        """Open a tracing span for a logical unit of work."""
        yield  # pragma: no cover

    @abstractmethod
    def log_event(
        self,
        event_name: str,
        payload: dict[str, Any],
        *,
        level: str = "info",
    ) -> None:
        """Emit a structured log event."""

    @abstractmethod
    def record_latency(self, operation: str, *, seconds: float) -> None:
        """Record how long an operation took."""

    @abstractmethod
    def increment_counter(self, metric: str, *, value: int = 1) -> None:
        """Increment a named counter."""

    @abstractmethod
    def record_error(
        self,
        error: Exception,
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Record an exception with optional context."""
