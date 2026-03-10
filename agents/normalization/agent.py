from __future__ import annotations

"""
NormalizationAgent implementation for the Job Intelligence Engine.

Phase 1 behavior:
    - Consumes `IngestBatch` events from the Ingestion Agent.
    - Loads raw records from `raw_ingested_jobs` for the given batch_id.
    - Maps each raw record into the canonical JobRecord shape:
        * Standardizes dates to ISO 8601.
        * Parses salary into (min, max, currency, period) when present.
        * Normalizes location strings.
        * Maps employment_type into the controlled vocabulary:
              full_time | part_time | contract | internship
        * Strips HTML and collapses whitespace in free-text fields.
    - Validates mapped records against the Pydantic JobRecord schema.
      * On validation failure: writes to `normalized_jobs` with
        validation_status = "quarantined" and annotated quarantine_reason.
      * Valid records are written with validation_status = "valid".
    - Tracks per-record latency using time.perf_counter() and logs
      median + p99 latency per batch via structlog.
    - On catastrophic batch failure, emits a `NormalizationFailed` event.
    - On success, emits a `NormalizationComplete` event.
"""

import os
import re
import statistics
import time
from datetime import datetime
from typing import Any, Iterable, List, Optional

import structlog
from pydantic import BaseModel, ValidationError
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.data_store.models import NormalizedJob, RawIngestedJob, Base


log = structlog.get_logger()


class SkillRecord(BaseModel):
    """Pydantic representation of a single skill within a JobRecord."""

    skill_id: Optional[str] = None
    label: str
    type: str  # Technical | Domain | Soft | Certification | Tool
    confidence: float
    field_source: str  # title | description | requirements | responsibilities
    required_flag: Optional[bool] = None


class JobRecord(BaseModel):
    """
    Canonical normalized job record schema (Phase 1).

    Mirrors the architecture definition for use during normalization.
    """

    # Identity
    external_id: str
    source: str  # "jsearch" | "crawl4ai"
    ingestion_run_id: str
    raw_payload_hash: str

    # Core
    title: str
    company: str
    location: Optional[str] = None
    salary_raw: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None  # annual | hourly | monthly
    employment_type: Optional[str] = None
    date_posted: Optional[datetime] = None
    description: Optional[str] = None

    # Skills Extraction output (populated later in the pipeline)
    skills: List[SkillRecord] = []
    extraction_status: Optional[str] = None  # ok | failed | partial

    # Phase 1 Enrichment output (placeholders for downstream)
    seniority: Optional[str] = None
    role_classification: Optional[str] = None
    sector_id: Optional[int] = None
    quality_score: Optional[float] = None
    is_spam: Optional[bool] = None
    spam_score: Optional[float] = None
    ai_relevance_score: Optional[float] = None
    company_id: Optional[int] = None
    location_id: Optional[int] = None
    overall_confidence: Optional[float] = None
    field_confidence: Optional[dict] = None


def _create_engine() -> Engine:
    """
    Construct a SQLAlchemy engine using the PYTHON_DATABASE_URL environment variable.

    The URL is expected to use the PostgreSQL + psycopg2 dialect.
    """
    database_url = os.getenv("PYTHON_DATABASE_URL")
    if not database_url:
        raise RuntimeError("PYTHON_DATABASE_URL is not set")

    log.info(
        "normalization_engine_create",
        url_scheme=database_url.split("://", 1)[0],
    )
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    return engine


ENGINE: Engine = _create_engine()
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)


class NormalizationAgent(BaseAgent):
    """
    NormalizationAgent maps raw ingested job postings into the canonical
    JobRecord schema and writes them to `normalized_jobs`.
    """

    def __init__(self) -> None:
        """Initialize the normalization agent with its canonical identifier."""
        super().__init__(agent_id="normalization")
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict[str, Any] = {}

    def health_check(self) -> dict:
        """
        Verify database connectivity for the normalization agent.

        Returns a dict conforming to the canonical health_check shape.
        """
        db_ok = False
        try:
            with ENGINE.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ok = True
        except SQLAlchemyError as exc:
            log.error("normalization_health_db_failed", error=str(exc))

        status = "ok" if db_ok else "down"
        if status == "ok":
            log.info("normalization_health_ok", agent=self.agent_id)
        else:
            log.error("normalization_health_down", agent=self.agent_id)

        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run_at.isoformat() if self._last_run_at else None,
            "metrics": self._last_run_metrics,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Consume an IngestBatch event and emit NormalizationComplete or NormalizationFailed.

        The inbound event's correlation_id is propagated unchanged.
        """
        batch_id = event.payload.get("batch_id")
        if not batch_id:
            log.error("normalization_missing_batch_id", payload_keys=list(event.payload.keys()))
            return self._emit_failed(
                inbound=event,
                error_type="missing_batch_id",
                error_reason="IngestBatch event missing batch_id",
            )

        latencies_ms: list[float] = []
        valid_count = 0
        quarantine_count = 0

        try:
            with SessionLocal() as session:
                raw_records = self._load_raw_records(session, batch_id)
                if not raw_records:
                    log.warning("normalization_no_raw_records", batch_id=batch_id)

                for raw_job in raw_records:
                    start = time.perf_counter()
                    try:
                        job_record = self._map_and_validate(raw_job)
                        self._write_normalized(session, job_record, raw_job, validation_status="valid")
                        valid_count += 1
                    except ValidationError as exc:
                        quarantine_count += 1
                        self._write_normalized(
                            session,
                            None,
                            raw_job,
                            validation_status="quarantined",
                            quarantine_reason=str(exc),
                        )
                        log.warning(
                            "normalization_record_quarantined",
                            batch_id=batch_id,
                        )
                    except Exception as exc:
                        quarantine_count += 1
                        self._write_normalized(
                            session,
                            None,
                            raw_job,
                            validation_status="quarantined",
                            quarantine_reason=str(exc),
                        )
                        log.error(
                            "normalization_record_error",
                            batch_id=batch_id,
                            error=str(exc),
                        )
                    finally:
                        elapsed_ms = (time.perf_counter() - start) * 1000.0
                        latencies_ms.append(elapsed_ms)

                session.commit()

        except SQLAlchemyError as exc:
            log.error(
                "normalization_batch_db_failure",
                batch_id=batch_id,
                error=str(exc),
            )
            return self._emit_failed(
                inbound=event,
                error_type="database_error",
                error_reason=str(exc),
            )
        except Exception as exc:
            log.error(
                "normalization_batch_unexpected_failure",
                batch_id=batch_id,
                error=str(exc),
            )
            return self._emit_failed(
                inbound=event,
                error_type="unknown_error",
                error_reason=str(exc),
            )

        # Compute median and p99 latency metrics.
        if latencies_ms:
            latencies_sorted = sorted(latencies_ms)
            median_ms = statistics.median(latencies_sorted)
            p99_index = max(int(len(latencies_sorted) * 0.99) - 1, 0)
            p99_ms = latencies_sorted[p99_index]
        else:
            median_ms = 0.0
            p99_ms = 0.0

        self._last_run_at = datetime.utcnow()
        self._last_run_metrics = {
            "batch_id": batch_id,
            "valid_count": valid_count,
            "quarantine_count": quarantine_count,
            "latency_median_ms": median_ms,
            "latency_p99_ms": p99_ms,
        }

        log.info(
            "normalization_latency_metrics",
            batch_id=batch_id,
            median_ms=median_ms,
            p99_ms=p99_ms,
            target_median_ms=200.0,
            target_p99_ms=1000.0,
        )

        payload = {
            "event_type": "NormalizationComplete",
            "batch_id": batch_id,
            "valid_count": valid_count,
            "quarantine_count": quarantine_count,
            "correlation_id": event.correlation_id,
        }
        outbound = EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
        return outbound

    def _load_raw_records(self, session: Session, batch_id: str) -> list[RawIngestedJob]:
        """
        Load all RawIngestedJob rows for a given ingestion_run_id.
        """
        rows = (
            session.execute(
                select(RawIngestedJob).where(RawIngestedJob.ingestion_run_id == batch_id)
            )
            .scalars()
            .all()
        )
        log.info(
            "normalization_loaded_raw_records",
            batch_id=batch_id,
            count=len(rows),
        )
        return rows

    def _map_and_validate(self, raw_job: RawIngestedJob) -> JobRecord:
        """
        Map a RawIngestedJob row into a JobRecord and validate it.

        Raises a ValidationError if the mapped record does not conform to the
        JobRecord schema.
        """
        meta = raw_job.raw_metadata_json or {}

        title_raw = meta.get("title") or ""
        company_raw = meta.get("company") or ""
        location_raw = meta.get("location")
        salary_raw = meta.get("salary_raw")
        description_raw = raw_job.raw_text or ""
        timestamp_raw = meta.get("timestamp")

        title = _normalize_whitespace(_strip_html(str(title_raw))) or "Unknown Title"
        company = _normalize_whitespace(_strip_html(str(company_raw))) or "Unknown Company"
        location = _normalize_whitespace(str(location_raw)) if location_raw else None

        salary_min, salary_max, salary_currency, salary_period = _parse_salary(str(salary_raw) if salary_raw else "")
        employment_type = _map_employment_type(raw_job.raw_text)
        description = _normalize_whitespace(_strip_html(description_raw)) or None
        date_posted = _parse_iso_datetime(timestamp_raw) if timestamp_raw else None

        job = JobRecord(
            external_id=raw_job.external_id,
            source=raw_job.source,
            ingestion_run_id=raw_job.ingestion_run_id,
            raw_payload_hash=raw_job.raw_payload_hash,
            title=title,
            company=company,
            location=location,
            salary_raw=str(salary_raw) if salary_raw else None,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            salary_period=salary_period,
            employment_type=employment_type,
            date_posted=date_posted,
            description=description,
        )
        return job

    def _write_normalized(
        self,
        session: Session,
        job_record: JobRecord | None,
        raw_job: RawIngestedJob,
        validation_status: str,
        quarantine_reason: str | None = None,
    ) -> None:
        """
        Persist a normalized job record to the normalized_jobs table.

        Both valid and quarantined records are written, with appropriate
        validation_status and quarantine_reason values.
        """
        if job_record is not None:
            title = job_record.title
            company = job_record.company
            location = job_record.location
            salary_min = job_record.salary_min
            salary_max = job_record.salary_max
            salary_currency = job_record.salary_currency
            salary_period = job_record.salary_period
            employment_type = job_record.employment_type
            date_posted = job_record.date_posted
            description = job_record.description
        else:
            # Fall back to raw metadata when validation fails.
            meta = raw_job.raw_metadata_json or {}
            title = _normalize_whitespace(_strip_html(str(meta.get("title") or ""))) or "Unknown Title"
            company = _normalize_whitespace(_strip_html(str(meta.get("company") or ""))) or "Unknown Company"
            location = _normalize_whitespace(str(meta.get("location"))) if meta.get("location") else None
            salary_min = None
            salary_max = None
            salary_currency = None
            salary_period = None
            employment_type = None
            date_posted = _parse_iso_datetime(meta.get("timestamp")) if meta.get("timestamp") else None
            description = None

        row = NormalizedJob(
            external_id=raw_job.external_id,
            source=raw_job.source,
            ingestion_run_id=raw_job.ingestion_run_id,
            raw_payload_hash=raw_job.raw_payload_hash,
            title=title,
            company=company,
            location=location,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            salary_period=salary_period,
            employment_type=employment_type,
            date_posted=date_posted,
            description=description,
            validation_status=validation_status,
            quarantine_reason=quarantine_reason,
        )
        session.add(row)

    def _emit_failed(
        self,
        inbound: EventEnvelope,
        error_type: str,
        error_reason: str,
    ) -> EventEnvelope:
        """
        Emit a NormalizationFailed event envelope for a failed batch.
        """
        payload = {
            "event_type": "NormalizationFailed",
            "correlation_id": inbound.correlation_id,
            "error_type": error_type,
            "error_reason": error_reason,
        }
        outbound = EventEnvelope(
            correlation_id=inbound.correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
        return outbound


def _strip_html(text: str) -> str:
    """
    Remove HTML tags from a string using a simple regex.
    """
    return re.sub(r"<[^>]+>", " ", text)


def _normalize_whitespace(text: str) -> str:
    """
    Collapse repeated whitespace characters into single spaces and trim ends.
    """
    return re.sub(r"\s+", " ", text).strip()


def _parse_iso_datetime(value: str | None) -> Optional[datetime]:
    """
    Parse a date/time string into a timezone-aware datetime when possible.
    """
    if not value:
        return None
    try:
        # Handle common Z-suffixed ISO timestamps.
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except Exception:
        log.warning("normalization_date_parse_failed", value=value)
        return None


def _parse_salary(salary_raw: str) -> tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
    """
    Best-effort salary parser for common textual patterns.

    Returns (salary_min, salary_max, salary_currency, salary_period).
    """
    if not salary_raw:
        return None, None, None, None

    # Extract numeric ranges like "80,000 - 100,000"
    numbers = [float(x.replace(",", "")) for x in re.findall(r"[0-9][0-9,]*", salary_raw)]
    if not numbers:
        return None, None, None, None

    if len(numbers) == 1:
        salary_min = salary_max = numbers[0]
    else:
        salary_min = min(numbers)
        salary_max = max(numbers)

    currency = None
    if "$" in salary_raw:
        currency = "USD"
    period = None
    lower = salary_raw.lower()
    if "per hour" in lower or "hourly" in lower:
        period = "hourly"
    elif "per month" in lower or "monthly" in lower:
        period = "monthly"
    elif "per year" in lower or "annual" in lower or "yearly" in lower or "/year" in lower:
        period = "annual"

    return salary_min, salary_max, currency, period


def _map_employment_type(raw_text: str) -> Optional[str]:
    """
    Map free-text mentions of employment type to the controlled vocabulary.
    """
    text_lower = raw_text.lower()
    if "full-time" in text_lower or "full time" in text_lower:
        return "full_time"
    if "part-time" in text_lower or "part time" in text_lower:
        return "part_time"
    if "intern" in text_lower:
        return "internship"
    if "contract" in text_lower or "contractor" in text_lower:
        return "contract"
    return None


