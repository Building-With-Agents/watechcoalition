"""
BaseAgent — the interface every agent in the pipeline must implement.

Week 2 walking skeleton: every agent extends this class and implements
health_check() and process().

Architecture rule: no agent may call another agent directly.
All inter-agent communication is through EventEnvelope objects only.
"""

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope


class BaseAgent:
    """
    Abstract base class for all Job Intelligence Engine agents.

    Subclasses MUST implement:
        health_check() -> dict
        process(event: EventEnvelope) -> EventEnvelope | None
    """

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id

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

    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """
        Consume an inbound EventEnvelope, perform this agent's work, and
        return an outbound EventEnvelope.

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
