"""
Normalization Agent — Week 3 Implementation.

Reads staged records from ``dbo.raw_ingested_jobs``, maps source fields to
canonical ``JobRecord`` schema, cleans text, parses salary/date/employment type,
validates, and writes to ``dbo.normalized_jobs``.

Agent ID (canonical): normalization-agent
Emits:    NormalizationComplete | NormalizationFailed
Consumes: IngestBatch
"""

from __future__ import annotations

import structlog
from pydantic import ValidationError

from agents.common.base_agent import BaseAgent
from agents.common.data_store.database import check_db_connection, session_scope
from agents.common.data_store.models import NormalizedJob, RawIngestedJob
from agents.common.event_envelope import EventEnvelope
from agents.normalization.cleaners import (
    clean_text,
    normalize_date,
    normalize_employment_type,
    normalize_location,
    parse_salary,
)
from agents.normalization.field_mappers.jsearch_mapper import JSearchMapper
from agents.normalization.field_mappers.scraper_mapper import ScraperMapper
from agents.normalization.schema.job_record import JobRecord

log = structlog.get_logger()

_MAPPERS = {
    "jsearch": JSearchMapper(),
    "crawl4ai": ScraperMapper(),
    "web_scrape": ScraperMapper(),
}


class NormalizationAgent(BaseAgent):
    """
    Normalizes raw ingested job records into canonical JobRecord format.

    Reads staged records from DB, applies source-specific field mapping,
    text cleaning, salary/date/employment normalization, validates via
    Pydantic, writes to normalized_jobs, and emits NormalizationComplete.
    """

    def __init__(self) -> None:
        super().__init__(agent_id="normalization-agent")

    def health_check(self) -> dict:
        """Check DB connectivity."""
        db_ok = check_db_connection()
        return {
            "status": "ok" if db_ok else "degraded",
            "agent": self.agent_id,
            "last_run": None,
            "metrics": {"db_connected": db_ok},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Normalize a batch of staged records.

        Consumes an IngestBatch event with ``staged_record_ids``.
        Emits NormalizationComplete or NormalizationFailed.
        """
        payload = event.payload
        staged_ids = payload.get("staged_record_ids", [])
        batch_id = payload.get("batch_id", "")

        log.info(
            "normalization_start",
            batch_id=batch_id,
            staged_count=len(staged_ids),
            correlation_id=event.correlation_id,
        )

        if not staged_ids:
            return EventEnvelope(
                correlation_id=event.correlation_id,
                agent_id=self.agent_id,
                payload={
                    "event_type": "NormalizationComplete",
                    "batch_id": batch_id,
                    "normalized_count": 0,
                    "quarantined_count": 0,
                    "normalization_status": "success",
                },
            )

        # Fetch staged records from DB
        try:
            with session_scope() as session:
                raw_records = (
                    session.query(RawIngestedJob)
                    .filter(RawIngestedJob.id.in_(staged_ids))
                    .all()
                )
                # Detach from session by reading all fields now
                records_data = [
                    {
                        "id": r.id,
                        "ingestion_run_id": r.ingestion_run_id,
                        "source": r.source,
                        "external_id": r.external_id,
                        "raw_payload_hash": r.raw_payload_hash,
                        "title": r.title,
                        "company": r.company,
                        "location": r.location,
                        "url": r.url,
                        "date_posted": r.date_posted,
                        "raw_text": r.raw_text,
                        "raw_payload": r.raw_payload,
                    }
                    for r in raw_records
                ]
        except Exception as exc:
            log.error("normalization_fetch_failed", batch_id=batch_id, error=str(exc))
            return EventEnvelope(
                correlation_id=event.correlation_id,
                agent_id=self.agent_id,
                payload={
                    "event_type": "NormalizationFailed",
                    "batch_id": batch_id,
                    "error": str(exc),
                },
            )

        normalized_count = 0
        quarantined_count = 0

        with session_scope() as session:
            for raw in records_data:
                try:
                    normalized = self._normalize_record(raw)

                    # Write to normalized_jobs
                    row = NormalizedJob(
                        raw_job_id=raw["id"],
                        ingestion_run_id=raw["ingestion_run_id"],
                        source=normalized.source,
                        external_id=normalized.external_id,
                        title=normalized.title,
                        company=normalized.company,
                        location=normalized.location,
                        normalized_location=normalized.normalized_location,
                        employment_type=normalized.employment_type.value if normalized.employment_type else None,
                        date_posted=normalized.date_posted,
                        salary_raw=normalized.salary_raw,
                        salary_min=normalized.salary_min,
                        salary_max=normalized.salary_max,
                        salary_currency=normalized.salary_currency,
                        salary_period=normalized.salary_period.value if normalized.salary_period else None,
                        description=normalized.description,
                        normalization_status="success",
                    )
                    session.add(row)
                    normalized_count += 1

                except (ValidationError, ValueError) as exc:
                    quarantined_count += 1
                    log.warning(
                        "normalization_quarantine",
                        external_id=raw.get("external_id"),
                        source=raw.get("source"),
                        error=str(exc),
                    )

        log.info(
            "normalization_complete",
            batch_id=batch_id,
            normalized_count=normalized_count,
            quarantined_count=quarantined_count,
        )

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "NormalizationComplete",
                "batch_id": batch_id,
                "normalized_count": normalized_count,
                "quarantined_count": quarantined_count,
                "normalization_status": "success" if quarantined_count == 0 else "partial",
            },
        )

    def _normalize_record(self, raw: dict) -> JobRecord:
        """Apply field mapping, cleaning, and validation to a single record."""
        source = raw.get("source", "")
        mapper = _MAPPERS.get(source, _MAPPERS["crawl4ai"])

        mapped = mapper.map(raw)

        # Clean text fields
        mapped["title"] = clean_text(mapped.get("title", ""))
        mapped["company"] = clean_text(mapped.get("company", ""))
        mapped["description"] = clean_text(mapped.get("description", ""))

        # Normalize date
        mapped["date_posted"] = normalize_date(mapped.get("date_posted"))

        # Normalize employment type
        mapped["employment_type"] = normalize_employment_type(
            mapped.pop("employment_type_raw", "")
        )

        # Normalize location
        mapped["normalized_location"] = normalize_location(mapped.get("location"))

        # Parse salary
        salary_raw = mapped.pop("salary_raw", None)
        salary = parse_salary(salary_raw)
        mapped["salary_raw"] = salary_raw
        mapped["salary_min"] = salary["salary_min"]
        mapped["salary_max"] = salary["salary_max"]
        mapped["salary_currency"] = salary["salary_currency"]
        mapped["salary_period"] = salary["salary_period"]

        # Carry identity fields from raw
        mapped["ingestion_run_id"] = raw.get("ingestion_run_id", "")
        mapped["raw_payload_hash"] = raw.get("raw_payload_hash", "")

        # Validate via Pydantic
        return JobRecord(**mapped)
