"""
LangSmithTracer — LangSmith concrete tracer implementation.
EXP-006 candidate: LangChain hosted tracing platform.
"""

from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from agents.common.tracer_base import TracerBase

try:
    from langsmith import Client
    _LANGSMITH_AVAILABLE = True
except ImportError:
    _LANGSMITH_AVAILABLE = False


class LangSmithTracer(TracerBase):
    """Tracer that sends spans and events to LangSmith."""

    def __init__(self, agent_id: str = "unknown-agent", project: str = "watechcoalition-exp006") -> None:
        self._agent_id = agent_id
        self._project = project
        self._client = Client() if _LANGSMITH_AVAILABLE else None
        self._runs: list[dict[str, Any]] = []

    @contextmanager
    def start_span(
        self,
        name: str,
        *,
        correlation_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        start = time.perf_counter()
        run_record: dict[str, Any] = {
            "name": name,
            "correlation_id": correlation_id,
            "agent_id": self._agent_id,
            "metadata": metadata or {},
            "status": "running",
            "events": [],
        }
        self._runs.append(run_record)
        try:
            yield None
            elapsed = time.perf_counter() - start
            run_record["status"] = "success"
            run_record["duration_seconds"] = round(elapsed, 4)
        except Exception as exc:
            elapsed = time.perf_counter() - start
            run_record["status"] = "error"
            run_record["duration_seconds"] = round(elapsed, 4)
            run_record["error"] = str(exc)
            raise

    def log_event(self, event_name: str, payload: dict[str, Any], *, level: str = "info") -> None:
        entry = {"event": event_name, "level": level, **payload}
        if self._runs:
            self._runs[-1]["events"].append(entry)

    def record_latency(self, operation: str, *, seconds: float) -> None:
        self.log_event("latency", {"operation": operation, "seconds": round(seconds, 4)})

    def increment_counter(self, metric: str, *, value: int = 1) -> None:
        self.log_event("counter", {"metric": metric, "value": value})

    def record_error(self, error: Exception, *, context: dict[str, Any] | None = None) -> None:
        entry = {"event": "error_recorded", "error": str(error), "error_type": type(error).__name__, **(context or {})}
        if self._runs:
            self._runs[-1]["events"].append(entry)
            self._runs[-1]["status"] = "error"

    def get_runs(self) -> list[dict[str, Any]]:
        return self._runs

    def clear_runs(self) -> None:
        self._runs.clear()
