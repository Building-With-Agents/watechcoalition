"""
Normalization Agent — stub. Consumes IngestBatch, emits NormalizationComplete. Writes to normalized_jobs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


def _agents_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _schema_dir() -> Path:
    return Path(__file__).resolve().parent / "schema"


class NormalizationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("normalization_agent")
        self._last_run: datetime | None = None

    def health_check(self) -> dict:
        schema_dir = _schema_dir()
        data_dir = _agents_root() / "data"
        ok = schema_dir.exists() and data_dir.exists()
        status = "ok" if ok else "degraded"
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {"schema_dir_exists": schema_dir.exists(), "data_dir_exists": data_dir.exists()},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        correlation_id = event.correlation_id
        inbound = event.payload or {}
        records = inbound.get("records", [])
        normalized = [
            {
                "external_id": r.get("url") or str(i),
                "source": r.get("source", "stub"),
                "title": r.get("title", ""),
                "company": r.get("company", ""),
                "location": r.get("location"),
                "description": r.get("raw_text"),
            }
            for i, r in enumerate(records)
        ]
        self._last_run = datetime.now(timezone.utc)
        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload={"records": normalized, "batch_id": correlation_id},
        )
