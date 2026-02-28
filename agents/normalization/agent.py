"""
Normalization Agent stub — Week 2 Walking Skeleton.

Real implementation: Week 3.

In the walking skeleton this agent receives an IngestBatch event and
returns a NormalizationComplete event.  No real transformation happens;
fields are passed through with stub normalized values added.

Agent ID (canonical): normalization-agent
Emits:    NormalizationComplete
Consumes: IngestBatch

Week 3 replaces this stub with:
- Per-source field mappers to canonical JobRecord schema
- ISO 8601 date standardisation
- Salary min/max/currency/period normalisation
- Location standardisation
- Employment type inference
- Schema-violation quarantine (bad records never pass downstream)
"""

from __future__ import annotations

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class NormalizationAgent(BaseAgent):
    """
    Stub for the Normalization Agent.

    Week 2: passes payload through with stub normalized fields added.
    Week 3: replaces this with real field mapping and schema enforcement.
    """

    def __init__(self) -> None:
        super().__init__(agent_id="normalization-agent")

    def health_check(self) -> dict:
        """Always ready — no external dependencies in stub mode."""
        return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Accept an IngestBatch event and emit a NormalizationComplete event.

        Stub adds normalized_location and employment_type fields.
        In Week 3, this is where field mapping and validation run.
        """
        p = event.payload

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "NormalizationComplete",
                "posting_id": p.get("posting_id"),
                "title": p.get("title"),
                "company": p.get("company"),
                "location": p.get("location"),
                "normalized_location": p.get("location"),   # stub: identity transform
                "employment_type": "full_time",             # stub: default
                "date_posted": p.get("timestamp"),
                "raw_text": p.get("raw_text"),
                "source": p.get("source"),
                "url": p.get("url"),
                "normalization_status": "success",
                # Week 3 adds: salary_min, salary_max, salary_currency, salary_period
            },
        )
