"""
Demand Analysis Agent stub — Week 2 Walking Skeleton.

THIS AGENT IS PHASE 2 ONLY.

It is included in the walking skeleton so the full eight-agent architecture
is visible and exercised from the beginning, but process() returns None.
The pipeline runner writes a "phase2_skipped" log entry for this agent so
that the run log still contains 80 entries (10 records x 8 agents).

Agent ID (canonical): demand-analysis-agent
Emits:    DemandSignalsUpdated  (Phase 2)
Consumes: RecordEnriched        (Phase 2)

Phase 2 replaces this stub with:
- Demand signal computation: skill velocity, role velocity, regional trends
- Salary forecasting
- Repost-rate analysis
- DemandSignalsUpdated event emission
"""

from __future__ import annotations

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class DemandAnalysisAgent(BaseAgent):
    """
    Stub for the Demand Analysis Agent (Phase 2 only).

    health_check() returns "down" — this agent is not active in Phase 1.
    process() returns None — the pipeline runner handles this gracefully
    by writing a "phase2_skipped" log entry rather than crashing.

    When Phase 2 begins, this stub is replaced with a real implementation
    that consumes RecordEnriched events and emits DemandSignalsUpdated.
    """

    def __init__(self) -> None:
        super().__init__(agent_id="demand-analysis-agent")

    def health_check(self) -> dict:
        """
        Returns down status — this agent is not yet implemented (Phase 2).

        The pipeline runner treats a non-"ok" status from a Phase 2 agent as
        a warning, not an abort condition.
        """
        return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> None:
        """
        Phase 2 stub — returns None.

        The pipeline runner skips None returns and writes a "phase2_skipped"
        log entry for this stage.  This keeps the run log at 80 entries
        (10 records x 8 agents) even though no real processing occurs.
        """
        return None  # Phase 2 — not yet implemented
