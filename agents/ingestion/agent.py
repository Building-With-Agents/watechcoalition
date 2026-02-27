# agents/ingestion/agent.py
"""Ingestion Agent — Phase 1. Emits IngestBatch. Writes to raw_ingested_jobs."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class IngestionAgent:
    """Poll JSearch (httpx) and Crawl4AI; dedup; stage to raw_ingested_jobs; emit IngestBatch."""

    def __init__(self) -> None:
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict[str, Any] = {}

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "agent": "ingestion",
            "last_run": self._last_run_at.isoformat() if self._last_run_at else "",
            "metrics": self._last_run_metrics,
        }

    def run(self, source: str | None = None, limit: int | None = None) -> None:
        """Run ingestion for source (jsearch | crawl4ai). Emit IngestBatch. TODO: implement."""
        raise NotImplementedError("IngestionAgent.run — Phase 1 implementation")
