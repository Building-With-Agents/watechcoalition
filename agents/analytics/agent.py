"""
Analytics Agent stub — Week 2 Walking Skeleton.

Real implementation: Week 7 (aggregates) + Week 8 (Ask the Data).

In the walking skeleton this agent returns the pre-computed batch analytics
fixture (fixture_analytics_refreshed.json) for every record it processes.
The fixture represents aggregate analytics across all 10 demo postings.

Note: in the walking skeleton, the same batch analytics payload is emitted
for every record processed.  In Week 7 the Analytics Agent accumulates data
across all records before emitting a single AnalyticsRefreshed event at
the end of a batch run.

Agent ID (canonical): analytics-agent
Emits:    AnalyticsRefreshed
Consumes: RecordEnriched

Fixture: agents/data/fixtures/fixture_analytics_refreshed.json

Week 7 replaces this stub with:
- Aggregation across 6 dimensions: skill, role, industry, region,
  experience level, company size
- Salary distributions: median, p25, p75, p95 per dimension
- Co-occurrence matrices
- Posting lifecycle metrics
- LLM-generated weekly summaries (deterministic template fallback)
- SQL guardrails: SELECT only, allowed tables, 100-row limit, 30s timeout
"""

from __future__ import annotations

import json
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

_FIXTURE_PATH = (
    Path(__file__).parent.parent / "data" / "fixtures" / "fixture_analytics_refreshed.json"
)


class AnalyticsAgent(BaseAgent):
    """
    Stub for the Analytics Agent.

    Week 2: returns batch-level fixture data for every record processed.
    Week 7: replaces this with real aggregate queries and LLM summaries.
    """

    def __init__(self) -> None:
        super().__init__(agent_id="analytics-agent")
        self._fixture: dict = {}

    def health_check(self) -> dict:
        """Return ok status if the fixture file is present and loadable."""
        if not _FIXTURE_PATH.exists():
            return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}
        try:
            self._fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
            return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}
        except Exception:
            return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Accept a RecordEnriched event and emit an AnalyticsRefreshed event
        using the pre-loaded batch-level fixture payload.

        In the walking skeleton the same aggregate payload is returned for
        every record.  Week 7 replaces this with real batch aggregation.
        """
        if not self._fixture:
            self._fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "AnalyticsRefreshed",
                "triggered_by_posting_id": event.payload.get("posting_id"),
                **self._fixture,
            },
        )
