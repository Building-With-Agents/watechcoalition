"""
Protocols (abstractions) for the pipeline. Use these for type hints and to satisfy SOLID.

BaseAgent is the canonical runtime contract. Keep this protocol for structural typing
in tests and helpers.
"""

from typing import Any, Protocol

from agents.common.events.base import AgentEvent


class Agent(Protocol):
    """
    Structural contract for every pipeline agent.

    BaseAgent satisfies this protocol and remains the canonical runtime base.
    """

    AGENT_ID: str  # class or instance attribute for logging

    def process(
        self,
        event: AgentEvent | None,
        correlation_id: str | None = None,
    ) -> AgentEvent | None:
        """Consume an input event (or None for Ingestion) and return the next event."""
        ...

    def health_check(self) -> dict[str, Any]:
        """Return status, agent id, last_run, metrics. Required on every agent."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe agent identity and common state."""
        ...

    def to_audit_dict(self) -> dict[str, Any]:
        """Return JSON-safe agent state for audit logging."""
        ...
