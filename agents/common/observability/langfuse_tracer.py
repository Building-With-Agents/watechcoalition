"""
LangfuseTracer — Langfuse concrete tracer implementation.
EXP-006 candidate: open-source LLM observability, hosted or self-hosted.

Sends real traces to Langfuse Cloud (or self-hosted) via the Langfuse Python SDK v4.
Env vars: LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_BASE_URL.
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
        self._active_observation: Any = None

    @contextmanager
    def start_span(
        self,
        name: str,
        *,
        correlation_id: str,
        input: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        if not self._client:
            yield None
            return

        span_metadata = {
            "agent_id": self._agent_id,
            **(metadata or {}),
        }

        try:
            with self._client.start_as_current_observation(
                name=f"{self._agent_id}/{name}",
                as_type="generation",
                model=span_metadata.get("model"),
                input=input,
                metadata=span_metadata,
            ) as observation:
                self._active_observation = observation
                try:
                    yield None
                except Exception as exc:
                    observation.update(
                        level="ERROR",
                        status_message=str(exc),
                    )
                    raise
                finally:
                    self._active_observation = None
        finally:
            # Flush to ensure trace is sent (non-blocking batch flush)
            try:
                self._client.flush()
            except Exception:
                pass

    def log_event(self, event_name: str, payload: dict[str, Any], *, level: str = "info") -> None:
        obs = self._active_observation
        if obs is None:
            return
        try:
            # Update the active generation with token/cost data when available
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
        obs = self._active_observation
        if obs is None:
            return
        try:
            obs.update(metadata={"latency_seconds": round(seconds, 4)})
        except Exception:
            pass

    def increment_counter(self, metric: str, *, value: int = 1) -> None:
        # Langfuse doesn't have native counters; record as metadata
        obs = self._active_observation
        if obs is None:
            return
        try:
            obs.update(metadata={f"counter_{metric}": value})
        except Exception:
            pass

    def record_error(self, error: Exception, *, context: dict[str, Any] | None = None) -> None:
        obs = self._active_observation
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

    def shutdown(self) -> None:
        """Flush pending traces and release resources."""
        if self._client:
            try:
                self._client.flush()
                self._client.shutdown()
            except Exception:
                pass
