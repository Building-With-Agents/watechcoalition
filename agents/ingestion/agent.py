"""
Ingestion Agent — stub. Emits IngestBatch. Phase 1: JSearch + Crawl4AI, dedup, raw_ingested_jobs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


def _agents_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _staging_dir() -> Path:
    return _agents_root() / "data" / "staging"


def _fallback_fixture_path() -> Path:
    return _agents_root() / "data" / "fixtures" / "fallback_scrape_sample.json"


class IngestionAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("ingestion_agent")
        self._last_run: datetime | None = None

    def health_check(self) -> dict:
        staging = _staging_dir()
        fixture = _fallback_fixture_path()
        if not staging.exists():
            staging.mkdir(parents=True, exist_ok=True)
        status = "down"
        if fixture.exists() and fixture.is_file():
            try:
                fixture.read_text(encoding="utf-8")
                status = "ok"
            except OSError:
                pass
        else:
            status = "degraded"
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {"staging_exists": staging.exists(), "fixture_readable": status == "ok"},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        correlation_id = event.correlation_id
        payload: dict = {"records": [], "source": "stub", "batch_id": correlation_id}
        fixture = _fallback_fixture_path()
        if fixture.exists():
            try:
                raw = json.loads(fixture.read_text(encoding="utf-8"))
                records = raw if isinstance(raw, list) else raw.get("records", [])
                payload = {"records": records[:5], "source": "stub", "batch_id": correlation_id}
            except (OSError, json.JSONDecodeError):
                pass
        self._last_run = datetime.now(timezone.utc)
        return EventEnvelope(correlation_id=correlation_id, agent_id=self.agent_id, payload=payload)
