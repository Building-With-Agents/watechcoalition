from __future__ import annotations

"""
IngestionAgent implementation for the Job Intelligence Engine.

Phase 1 behavior (fixture-based):
    - Accepts a source configuration (name, type, URL).
    - On process(), creates a `job_ingestion_runs` record with status "running".
    - Loads raw job postings from `agents/data/fixtures/fallback_scrape_sample.json`.
    - Computes a deterministic fingerprint per record:
          sha256(source + external_id + title + company + date_posted)
    - Deduplicates against `raw_ingested_jobs.raw_payload_hash`, honoring the rule
      that JSearch wins over scraped data when a duplicate exists.
    - Inserts non-duplicate records into `raw_ingested_jobs`.
    - Updates the `job_ingestion_runs` record to "complete" with final counts.
    - Emits an `IngestBatch` `EventEnvelope` on success.
    - On source failure, retries with exponential back-off (max 5 attempts),
      then emits a `SourceFailure` event and marks the run as "failed".
    - On schema violations at intake, writes the offending record to
      `agents/data/dead_letter/` and continues processing the batch.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from agents.common.base_agent import BaseAgent
from agents.common.data_store.models import Base, JobIngestionRun, RawIngestedJob
from agents.common.event_envelope import EventEnvelope

log = structlog.get_logger()


def _create_engine() -> Engine:
    """
    Construct a SQLAlchemy engine using the PYTHON_DATABASE_URL environment variable.

    The URL is expected to use the PostgreSQL + psycopg2 dialect, e.g.:
        postgresql+psycopg2://user:password@host:5432/dbname
    """
    database_url = os.getenv("PYTHON_DATABASE_URL")
    if not database_url:
        raise RuntimeError("PYTHON_DATABASE_URL is not set")

    # The URL itself may contain credentials; avoid logging them.
    log.info(
        "ingestion_engine_create",
        url_scheme=database_url.split("://", 1)[0],
    )
    engine = create_engine(database_url, future=True)
    # Ensure tables exist (idempotent; uses metadata definitions).
    Base.metadata.create_all(engine)
    return engine


ENGINE: Engine = _create_engine()
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)


@dataclass
class SourceConfig:
    """
    Configuration for an ingestion source.

    Attributes
    ----------
    name:
        Logical name of the source (e.g. "crawl4ai", "jsearch").
    type:
        Source type (e.g. "web_scrape", "jsearch").
    url:
        Base URL or descriptor for the source. In Phase 1 this is informational,
        since we rely on local fixture data instead of live HTTP calls.
    """

    name: str
    type: str
    url: str


class IngestionAgent(BaseAgent):
    """
    IngestionAgent reads raw job postings from a configured source and stages
    them into the `raw_ingested_jobs` table while tracking batch-level metrics.
    """

    def __init__(self, source: SourceConfig) -> None:
        """
        Initialize the ingestion agent with its canonical identifier and source.
        """
        super().__init__(agent_id="ingestion")
        self.source = source
        self._fixtures_dir = (
            Path(__file__).resolve().parent.parent / "data" / "fixtures"
        )
        self._fixture_path = self._fixtures_dir / "fallback_scrape_sample.json"
        self._dead_letter_dir = (
            Path(__file__).resolve().parent.parent / "data" / "dead_letter"
        )
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict[str, Any] = {}

    def health_check(self) -> dict:
        """
        Validate database connectivity and fixture availability.

        Returns a dict with:
            - status: "ok" if both DB and fixture are available, otherwise "down"
            - agent: agent identifier
            - last_run: ISO-8601 timestamp of last successful run, or None
            - metrics: last recorded metrics, if any
        """
        db_ok = False
        fixture_ok = self._fixture_path.exists()

        try:
            with ENGINE.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ok = True
        except SQLAlchemyError as exc:
            log.error("ingestion_health_db_failed", error=str(exc))

        status = "ok" if (db_ok and fixture_ok) else "down"

        if status == "ok":
            log.info(
                "ingestion_health_ok",
                agent=self.agent_id,
                db_ok=db_ok,
                fixture_path=str(self._fixture_path),
            )
        else:
            log.error(
                "ingestion_health_down",
                agent=self.agent_id,
                db_ok=db_ok,
                fixture_exists=fixture_ok,
                fixture_path=str(self._fixture_path),
            )

        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run_at.isoformat() if self._last_run_at else None,
            "metrics": self._last_run_metrics,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Process an inbound event and emit an IngestBatch or SourceFailure event.

        The inbound `EventEnvelope`'s `correlation_id` is propagated unchanged
        to the outbound event.
        """
        start_time = datetime.now(UTC)
        run_id: str | None = None
        session: Session
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
        batch_payload = {
            "event_type": "IngestBatch",
            "batch_id": run_id,
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

    def _load_records_with_retry(self) -> list[dict[str, Any]]:
        """
        Load raw job records from the fixture file with exponential back-off.

        On repeated failure (5 attempts), raises SourceFailureError so that the
        caller can emit a SourceFailure event and mark the run as failed.
        """
        max_attempts = 5
        delay_seconds = 1.0

        for attempt in range(1, max_attempts + 1):
            try:
                raw_text = self._fixture_path.read_text(encoding="utf-8")
                data = json.loads(raw_text)
                if not isinstance(data, list):
                    raise ValueError("fixture_data_not_list")
                log.info(
                    "ingestion_fixture_loaded",
                    path=str(self._fixture_path),
                    record_count=len(data),
                )
                return data
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                log.warning(
                    "ingestion_fixture_load_failed",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=str(exc),
                )
                if attempt == max_attempts:
                    raise SourceFailureError("max_attempts_exceeded") from exc
                time.sleep(delay_seconds)
                delay_seconds *= 2

        # Unreachable, but keeps type checkers satisfied.
        raise SourceFailureError("unreachable_retry_loop_exhausted")

    def _process_single_record(
        self,
        session: Session,
        run: JobIngestionRun,
        raw_record: dict[str, Any],
    ) -> str:
        """
        Process a single raw record: deduplication and staging insert.

        Returns
        -------
        str
            "ingested" if the record was inserted,
            "dedup" if it was identified as a duplicate and discarded,
            or raises an exception on schema violation.
        """
        # Basic schema validation — raise for missing critical fields.
        external_id = str(raw_record["posting_id"])
        title = str(raw_record["title"])
        company = str(raw_record["company"])
        # date_posted may be absent; treat as empty string in fingerprint if so.
        timestamp_str = str(raw_record.get("timestamp", "") or "")

        fingerprint = self._fingerprint(
            source=self.source.name,
            external_id=external_id,
            title=title,
            company=company,
            date_posted=timestamp_str,
        )

        # Deduplication: check for existing record with same fingerprint.
        existing = session.execute(
            select(RawIngestedJob).where(RawIngestedJob.raw_payload_hash == fingerprint)
        ).scalar_one_or_none()

        if existing is not None:
            # JSearch wins over scraped when both exist.
            if self.source.type.lower() == "jsearch" and existing.source.lower() != "jsearch":
                existing.source = self.source.name
                existing.raw_text = str(raw_record.get("raw_text", ""))
                existing.raw_metadata_json = self._build_metadata(raw_record, external_id)
                session.flush()
                log.info(
                    "ingestion_jsearch_overwrites_scrape",
                    run_id=str(run.id),
                )
                return "ingested"

            # Duplicate from same or lower-priority source: discard silently.
            return "dedup"

        # Insert new raw_ingested_jobs row.
        job = RawIngestedJob(
            source=self.source.name,
            external_id=external_id,
            raw_payload_hash=fingerprint,
            ingestion_run_id=str(run.id),
            raw_text=str(raw_record.get("raw_text", "")),
            raw_metadata_json=self._build_metadata(raw_record, external_id),
        )
        session.add(job)
        session.flush()
        return "ingested"

    @staticmethod
    def _fingerprint(
        source: str,
        external_id: str,
        title: str,
        company: str,
        date_posted: str,
    ) -> str:
        """
        Compute the canonical fingerprint for a job posting.

        The fingerprint is defined as:
            sha256(source + external_id + title + company + date_posted)
        """
        key = f"{source}{external_id}{title}{company}{date_posted}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_metadata(
        raw_record: dict[str, Any],
        external_id: str,
    ) -> dict[str, Any]:
        """
        Construct a metadata JSON document for a raw ingested job record.

        Only non-PII fields are included; free-text is stored in `raw_text`.
        """
        return {
            "posting_id": external_id,
            "source": raw_record.get("source"),
            "url": raw_record.get("url"),
            "timestamp": raw_record.get("timestamp"),
            "location": raw_record.get("location"),
        }

    def _write_dead_letter(self, raw_record: dict[str, Any], reason: str) -> None:
        """
        Persist a schema-violating or otherwise unprocessable record to dead_letter.

        The filename includes a UTC timestamp to avoid collisions.
        """
        self._dead_letter_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        filename = f"ingestion_dead_{timestamp}.json"
        path = self._dead_letter_dir / filename

        try:
            payload = {"record": raw_record, "reason": reason}
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            log.info(
                "ingestion_dead_letter_written",
                path=str(path),
            )
        except OSError as exc:
            log.error(
                "ingestion_dead_letter_write_failed",
                path=str(path),
                error=str(exc),
            )


class SourceFailureError(RuntimeError):
    """Raised when the ingestion source is unavailable after retries."""


