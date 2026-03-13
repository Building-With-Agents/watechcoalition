"""
Normalization Agent — maps raw records from IngestBatch to canonical JobRecord.

Consumes IngestBatch (with optional records array); applies per-source mapper (JSearch);
emits NormalizationComplete with batch_id, record_count, quarantine_count, and normalized records.

Agent ID (canonical): normalization-agent
Emits:    NormalizationComplete
Consumes: IngestBatch
"""

from __future__ import annotations

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.types.raw_job_record import RawJobRecord
from agents.normalization.mappers.jsearch_mapper import JSearchMapper

log = structlog.get_logger()


def _dict_to_raw_record(record: dict) -> RawJobRecord | None:
    """Build RawJobRecord from IngestBatch record dict (full or legacy shape)."""
    if not record:
        return None
    # Full RawJobRecord shape (from JSearch adapter)
    if "external_id" in record and "source" in record and "title" in record:
        try:
            return RawJobRecord.model_validate(record)
        except Exception:
            pass
    # Legacy single-posting shape
    title = (record.get("title") or "").strip() or "Untitled"
    company = (record.get("company") or "").strip() or "Unknown"
    return RawJobRecord(
        external_id=str(record.get("external_id") or record.get("posting_id") or ""),
        source=record.get("source", "web_scrape"),
        region_id="",
        raw_payload_hash=record.get("raw_payload_hash", ""),
        title=title,
        company=company,
        description=record.get("raw_text", ""),
        job_url=record.get("url"),
        date_posted=None,
    )


class NormalizationAgent(BaseAgent):
    """Normalization Agent: maps raw records to canonical JobRecord, emits NormalizationComplete."""

    def __init__(self) -> None:
        self._jsearch_mapper = JSearchMapper()

    @property
    def agent_id(self) -> str:
        return "normalization-agent"

    def health_check(self) -> dict:
        return {
            "status": "ok",
            "agent": self.agent_id,
            "last_run": None,
            "metrics": {},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """
        Accept an IngestBatch event. If payload has records, map each to JobRecord
        and emit NormalizationComplete with batch metadata and normalized records.
        Otherwise emit NormalizationComplete with stub fields (legacy single-posting).
        """
        p = event.payload or {}
        records = p.get("records")
        batch_id = p.get("batch_id", "")
        source = p.get("source", "web_scrape")

        if records and isinstance(records, list):
            normalized: list[dict] = []
            quarantine_count = 0
            for rec in records:
                if not isinstance(rec, dict):
                    quarantine_count += 1
                    continue
                raw = _dict_to_raw_record(rec)
                if raw is None:
                    quarantine_count += 1
                    continue
                try:
                    job = self._jsearch_mapper.map(raw)
                    normalized.append(job.model_dump(mode="json"))
                except Exception as ex:
                    log.warning("normalization_failed", external_id=raw.external_id, error=str(ex))
                    quarantine_count += 1
            record_count = len(normalized)
            payload = {
                "event_type": "NormalizationComplete",
                "batch_id": batch_id,
                "record_count": record_count,
                "quarantine_count": quarantine_count,
                "source": source,
                "normalized_records": normalized,
            }
            return EventEnvelope(
                correlation_id=event.correlation_id,
                agent_id=self.agent_id,
                payload=payload,
            )

        # Legacy: single-posting payload without records list
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "NormalizationComplete",
                "batch_id": batch_id or "legacy-1",
                "record_count": 1,
                "quarantine_count": 0,
                "posting_id": p.get("posting_id"),
                "title": p.get("title"),
                "company": p.get("company"),
                "location": p.get("location"),
                "normalized_location": p.get("location"),
                "employment_type": "full_time",
                "date_posted": p.get("timestamp"),
                "raw_text": p.get("raw_text"),
                "source": p.get("source"),
                "url": p.get("url"),
                "normalization_status": "success",
            },
        )
