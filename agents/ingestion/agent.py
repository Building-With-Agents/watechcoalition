"""Ingestion agent — ingests from JSearch and Crawl4AI, deduplicates, stages to raw_ingested_jobs."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class IngestionAgent(BaseAgent):
    """
    Consumes raw posting; adds provenance; emits IngestBatch.
    Phase 1: fingerprint, dedup, provenance tags. Walking skeleton: payload shaping only.
    """

    def __init__(self, agent_id: str = "ingestion") -> None:
        super().__init__(agent_id=agent_id)
        self.last_run_at: Optional[datetime] = None
        self.last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return agent readiness: status, agent, last_run, metrics (architecture contract)."""
        return {
            "status": "ok",
            "agent": self.agent_id,
            "last_run": self.last_run_at.isoformat() if self.last_run_at else None,
            "metrics": self.last_run_metrics,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Build IngestBatch payload: copy inbound fields and add provenance.
        Walking skeleton: no DB write; payload shaping only.
        """
        payload = event.payload
        title = payload.get("title", "")
        company = payload.get("company", "")
        raw_payload_hash = hashlib.sha256(
            f"{payload.get('source', '')}{payload.get('posting_id', '')}{title}{company}{payload.get('timestamp', '')}".encode()
        ).hexdigest()
        ingestion_run_id = "skeleton-run-001"
        ingestion_timestamp = datetime.utcnow().isoformat() + "Z"
        external_id = str(payload.get("posting_id", ""))

        out_payload = dict(payload)
        out_payload["external_id"] = external_id
        out_payload["raw_payload_hash"] = raw_payload_hash
        out_payload["ingestion_run_id"] = ingestion_run_id
        out_payload["ingestion_timestamp"] = ingestion_timestamp

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=out_payload,
        )


default_agent = IngestionAgent(agent_id="ingestion")


def health_check() -> dict:
    """Return agent health status. Required on every agent. Backward-compatible module-level API."""
    return default_agent.health_check()
