"""
InstrumentedIngestionAgent — Ingestion Agent with TracerBase instrumentation.
EXP-006: same agent logic as agent.py, wrapped with full observability.
"""

from __future__ import annotations

import time
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.tracer_base import TracerBase

_FIXTURES_DIR = Path(__file__).parent.parent / "data" / "fixtures"
_FALLBACK_SCRAPE = _FIXTURES_DIR / "fallback_scrape_sample.json"


class InstrumentedIngestionAgent(BaseAgent):
    """Ingestion Agent instrumented with a pluggable TracerBase implementation."""

    def __init__(self, tracer: TracerBase) -> None:
        super().__init__(agent_id="ingestion-agent")
        self._tracer = tracer

    def health_check(self) -> dict:
        if _FALLBACK_SCRAPE.exists():
            return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}
        return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        correlation_id = event.correlation_id

        with self._tracer.start_span(
            "ingest_batch",
            correlation_id=correlation_id,
            metadata={"agent_id": self.agent_id},
        ):
            self._tracer.log_event(
                "batch_started",
                {"correlation_id": correlation_id, "source": event.payload.get("source", "unknown")},
            )

            fetch_start = time.perf_counter()
            raw = event.payload
            self._tracer.record_latency("source_fetch", seconds=time.perf_counter() - fetch_start)

            dedup_start = time.perf_counter()
            raw_hash = "stub-hash"
            self._tracer.record_latency("dedup_check", seconds=time.perf_counter() - dedup_start)

            dedup_count = raw.get("dedup_count", 0)
            if dedup_count:
                self._tracer.increment_counter("dedup_count", value=dedup_count)

            if raw.get("simulate_error"):
                exc = ValueError(f"SourceFailure: {raw.get('simulate_error')}")
                self._tracer.record_error(
                    exc,
                    context={"source": raw.get("source", "unknown"), "correlation_id": correlation_id},
                )
                raise exc

            result = EventEnvelope(
                correlation_id=correlation_id,
                agent_id=self.agent_id,
                payload={
                    "event_type": "IngestBatch",
                    "posting_id": raw.get("posting_id"),
                    "source": raw.get("source", "web_scrape"),
                    "url": raw.get("url"),
                    "title": raw.get("title"),
                    "company": raw.get("company"),
                    "location": raw.get("location"),
                    "timestamp": raw.get("timestamp"),
                    "raw_text": raw.get("raw_text"),
                    "ingestion_run_id": correlation_id,
                    "ingestion_timestamp": event.timestamp.isoformat(),
                    "raw_payload_hash": raw_hash,
                    "external_id": str(raw.get("posting_id")),
                },
            )

            self._tracer.log_event(
                "batch_complete",
                {"correlation_id": correlation_id, "event_type": "IngestBatch"},
            )

            return result
