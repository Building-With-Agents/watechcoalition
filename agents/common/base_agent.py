"""
BaseAgent — the canonical runtime contract for every pipeline agent.

All pipeline agents must extend this class, implement `health_check()` and
`process()`, and exchange `AgentEvent` objects only. The base provides safe
JSON serialization helpers for audit logging and future LLM context.

Subclasses should store their last run timestamp on either `_last_run` or
`last_run_at`. Optional metrics may be exposed via `metrics`,
`last_run_metrics`, or `_metrics`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from agents.common.events.base import AgentEvent


class BaseAgent:
    """
    Abstract base class for all Job Intelligence Engine agents.

    Subclasses MUST implement:
        health_check() -> dict
        process(event: AgentEvent | None, correlation_id: str | None = None)
            -> AgentEvent | None
    """

    AGENT_ID: str = ""

    def __init__(self, agent_id: str) -> None:
        if not agent_id:
            raise ValueError("agent_id must be a non-empty string")
        if self.AGENT_ID and agent_id != self.AGENT_ID:
            raise ValueError(
                f"{self.__class__.__name__} AGENT_ID {self.AGENT_ID!r} "
                f"does not match instance id {agent_id!r}"
            )
        self.agent_id = agent_id

    @staticmethod
    def _json_ready(value: Any) -> Any:
        """Recursively convert common runtime values into JSON-safe data."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(key): BaseAgent._json_ready(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [BaseAgent._json_ready(item) for item in value]
        return value

    def _last_run_value(self) -> Any:
        """Return the common last-run attribute used across agent implementations."""
        for attr in ("last_run_at", "_last_run"):
            value = getattr(self, attr, None)
            if value is not None:
                return value
        return None

    def _metrics_value(self) -> dict[str, Any]:
        """Return common metrics attributes when subclasses expose them."""
        for attr in ("last_run_metrics", "metrics", "_metrics"):
            value = getattr(self, attr, None)
            if isinstance(value, dict):
                return value
        return {}

    def to_dict(self) -> dict[str, Any]:
        """
        Return JSON-safe identity and shared runtime state for this agent.

        Subclasses can override this to add fields, but should keep values
        JSON-serializable.
        """
        return {
            "agent_id": self.agent_id,
            "last_run": self._json_ready(self._last_run_value()),
            "metrics": self._json_ready(self._metrics_value()),
        }

    def to_audit_dict(self) -> dict[str, Any]:
        """
        Return a compact audit payload for orchestration logging or LLM context.

        The payload intentionally excludes agent-private attributes so it can be
        logged safely without leaking unrelated runtime state.
        """
        audit = {
            "agent_id": self.agent_id,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        audit.update(self.to_dict())
        try:
            health = self.health_check()
        except Exception as exc:  # pragma: no cover - defensive path
            audit["status"] = "unknown"
            audit["health_error"] = type(exc).__name__
        else:
            audit["status"] = health.get("status", "unknown")
        return audit

    def health_check(self) -> dict:
        """
        Return a dict describing agent readiness.

        Expected shape:
            {
                "status": "ok" | "degraded" | "down",
                "agent": self.agent_id,
                "last_run": <ISO datetime or None>,
                "metrics": <dict of agent-specific metrics>
            }

        The pipeline runner checks result["status"] == "ok" before
        processing any records.  If any Phase 1 agent returns a non-"ok"
        status, the pipeline aborts.  Phase 2 agents returning non-"ok"
        produce a warning, not an abort.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement health_check()"
        )

    def process(
        self,
        event: AgentEvent | None,
        correlation_id: str | None = None,
    ) -> AgentEvent | None:
        """
        Consume an inbound AgentEvent, perform this agent's work, and return
        an outbound AgentEvent.

        Rules:
        - The outbound event MUST carry the same correlation_id as the
          inbound event.
        - The agent_id in the outbound event must equal self.agent_id.
        - Return None ONLY for Phase 2 agents not yet implemented.
          The pipeline runner handles None returns gracefully.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement process()"
        )
