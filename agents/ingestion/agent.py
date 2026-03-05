"""
Ingestion Agent — stub: reads one job from fixture and emits IngestBatch.

Production: JSearch + Crawl4AI, dedup, raw_ingested_jobs. See PIPELINE_DESIGN.md.
"""

import json
from datetime import UTC, datetime

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.config import ENV_PIPELINE_INPUT, get_fixture_path
from agents.common.events.base import SCHEMA_VERSION, AgentEvent, create_event

log = structlog.get_logger()


class IngestionAgent(BaseAgent):
    AGENT_ID = "ingestion"
    """Stub: reads fallback_scrape_sample.json, wraps one record in IngestBatch."""

    def __init__(self) -> None:
        super().__init__(self.AGENT_ID)
        self._last_run: datetime | None = None

    def process(
        self,
        event: AgentEvent | None,
        correlation_id: str | None = None,
    ) -> AgentEvent | None:
        """
        Ingestion has no upstream event; runner passes None and correlation_id.
        Returns one AgentEvent with IngestBatch payload (list of raw job records).
        """
        self._last_run = datetime.now(UTC)
        cid = correlation_id or (event.correlation_id if event else None)
        if not cid:
            log.warning("ingestion_missing_correlation_id")
            return None

        path = get_fixture_path(ENV_PIPELINE_INPUT, "fallback_scrape_sample.json")
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            log.warning("ingestion_fixture_read_failed", path=str(path), error_type=type(e).__name__)
            return None

        records = data if isinstance(data, list) else [data]
        first = records[0] if records else {}
        ev = create_event(cid, self.agent_id, SCHEMA_VERSION, {"jobs": [first]})
        log.debug("ingestion_emitted", event_id=ev.event_id, correlation_id=ev.correlation_id, job_count=1)
        return ev

    def health_check(self) -> dict:
        return {
            "status": "ok",
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {},
        }
