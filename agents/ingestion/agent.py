"""
Ingestion Agent stub — Week 2 Walking Skeleton.

Real implementation: Week 3.

In the walking skeleton this agent receives the raw job posting payload
(loaded from the fallback scrape file by the pipeline runner) and wraps it
in an IngestBatch event, adding stub provenance metadata.

Agent ID (canonical): ingestion-agent
Emits:    IngestBatch
Consumes: (initial pipeline input — raw posting dict as payload)

Week 3 replaces this stub with:
- Real JSearch API ingestion via httpx
- Web scraping via Crawl4AI
- SHA-256 deduplication fingerprint
- Full provenance tagging
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.data_store import get_session_factory
from agents.common.data_store.models import JobIngestionRun
from agents.common.event_envelope import EventEnvelope

log = structlog.get_logger()
SessionLocal = get_session_factory()


class SourceFailureError(Exception):
    """Raised when the ingestion source is unreachable after retries."""
    pass

# The fallback scrape file lives alongside the other fixtures.
# health_check() verifies it exists before the pipeline runs.
_FIXTURES_DIR = Path(__file__).parent.parent / "data" / "fixtures"
_FALLBACK_SCRAPE = _FIXTURES_DIR / "fallback_scrape_sample.json"


class IngestionAgent(BaseAgent):
    """
    Stub for the Ingestion Agent.

    Week 2: wraps raw posting data in a typed IngestBatch event envelope.
    Week 3: replaces this with real API + scraping, dedup, and provenance tags.
    """

    @property
    def agent_id(self) -> str:
        return "ingestion-agent"

    def health_check(self) -> dict:
        """Return ok status if the fallback scrape file is present and readable."""
        if _FALLBACK_SCRAPE.exists():
            return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}
        return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Accept a raw posting payload and emit an IngestBatch event.

        The raw payload is passed through unchanged.  In Week 3 this is
        where source-field normalisation, dedup fingerprinting, and
        provenance tagging happen.
        """
        start_time = datetime.now(UTC)
        run_id: str | None = None
        record_count = 0
        dedup_count = 0
        error_count = 0

        try:
            with SessionLocal() as session:
                # 1. Create job_ingestion_runs record (status: running)
                run = JobIngestionRun(
                    source=self.source.name,
                    status="running",
                )
                session.add(run)
                session.flush()  # populate PK
                run_id = str(run.id)

                log.info(
                    "ingestion_run_started",
                    agent=self.agent_id,
                    run_id=run_id,
                    source=self.source.name,
                )

                # 2. Load fixture records with retry handling for source failures.
                records = self._load_records_with_retry()

                # 3. Process each record: dedup + insert.
                for raw_record in records:
                    try:
                        processed = self._process_single_record(
                            session=session,
                            run=run,
                            raw_record=raw_record,
                        )
                    except Exception as exc:  # schema violation or unexpected error
                        error_count += 1
                        self._write_dead_letter(raw_record, reason=str(exc))
                        log.error(
                            "ingestion_record_error",
                            agent=self.agent_id,
                            run_id=run_id,
                            error=str(exc),
                        )
                        continue

                    if processed == "dedup":
                        dedup_count += 1
                    elif processed == "ingested":
                        record_count += 1

                # 4. Update run record to complete with final counts.
                run.status = "complete"
                run.record_count = record_count
                run.dedup_count = dedup_count
                run.error_count = error_count
                run.completed_at = datetime.now(UTC)
                session.commit()

                self._last_run_at = run.completed_at
                self._last_run_metrics = {
                    "record_count": record_count,
                    "dedup_count": dedup_count,
                    "error_count": error_count,
                }

                log.info(
                    "ingestion_run_complete",
                    agent=self.agent_id,
                    run_id=run_id,
                    record_count=record_count,
                    dedup_count=dedup_count,
                    error_count=error_count,
                )

        except SourceFailureError as exc:
            # Source failures are handled by emitting a SourceFailure event and
            # marking the run as failed when possible.
            if run_id is not None:
                with SessionLocal() as session:
                    run = session.get(JobIngestionRun, run_id)
                    if run is not None:
                        run.status = "failed"
                        run.error_count = run.error_count + 1
                        run.completed_at = datetime.now(UTC)
                        session.commit()

            log.error(
                "ingestion_source_failure",
                agent=self.agent_id,
                run_id=run_id,
                source=self.source.name,
                error=str(exc),
            )

            payload = {
                "event_type": "SourceFailure",
                "source": self.source.name,
                "run_id": run_id,
                "error": "source_unavailable",
            }
            outbound = EventEnvelope(
                correlation_id=event.correlation_id,
                agent_id=self.agent_id,
                payload=payload,
            )
            return outbound

        # Success path: emit IngestBatch event.
        elapsed_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        total_fetched = record_count + dedup_count + error_count
        batch_payload = {
            "event_type": "IngestBatch",
            "batch_id": run_id,
            "total_fetched": total_fetched,
            "record_count": record_count,
            "dedup_count": dedup_count,
            "source": self.source.name,
            "correlation_id": event.correlation_id,
            "elapsed_ms": elapsed_ms,
        }
        outbound = EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=batch_payload,
        )
        log.info(
            "ingestion_emit_ingest_batch",
            agent=self.agent_id,
            run_id=run_id,
            record_count=record_count,
            dedup_count=dedup_count,
        )
        return outbound
