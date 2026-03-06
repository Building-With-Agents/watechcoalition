"""AgentBase — the abstract base every agent in the pipeline must implement.

Contract type: Architectural (Fixed) — students extend this class
but do NOT modify its interface.

Week 2 walking skeleton: every agent extends this class and implements
health_check() and process().

Architecture rule: no agent may call another agent directly.
All inter-agent communication is through EventEnvelope objects only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agents.common.event_envelope import EventEnvelope


class AgentBase(ABC):
    """Abstract base class for all Job Intelligence Engine agents.

    Subclasses MUST implement:
        agent_id (property) -> str
        health_check() -> dict
        process(event: EventEnvelope) -> EventEnvelope | None
    """

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Canonical agent identifier (e.g. 'ingestion-agent')."""
        ...

    @abstractmethod
    def health_check(self) -> dict:
        """Return a dict describing agent readiness.

        Expected shape:
            {
                "status": "ok" | "degraded" | "down",
                "agent": self.agent_id,
                "last_run": <ISO datetime or None>,
                "metrics": <dict of agent-specific metrics>
            }
        """

    @abstractmethod
    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """Consume an inbound EventEnvelope, perform this agent's work,
        and return an outbound EventEnvelope.

        Rules:
        - The outbound event MUST carry the same correlation_id as the
          inbound event.
        - The agent_id in the outbound event must equal self.agent_id.
        - Return None ONLY for Phase 2 agents not yet implemented.
        """


# Backward-compatibility alias
BaseAgent = AgentBase
