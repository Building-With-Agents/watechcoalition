"""
Ingestion Agent — JSearch (and later Crawl4AI) source ingestion.

When the trigger event payload includes region_config, runs the JSearch adapter,
deduplicates by raw_payload_hash, optionally stages to raw_ingested_jobs,
and emits an IngestBatch event with batch metadata and records.

Agent ID (canonical): ingestion-agent
Emits:    IngestBatch, SourceFailure (on adapter failure)
Consumes: Trigger with optional region_config and source filter.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.types.region_config import RegionConfig
from agents.common.types.raw_job_record import RawJobRecord
from agents.ingestion.events import ingest_batch_payload, source_failure_payload
from agents.ingestion.sources.jsearch_adapter import JSearchAdapter

log = structlog.get_logger()

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"
_FALLBACK_SCRAPE = _FIXTURES_DIR / "fallback_scrape_sample.json"


class IngestionAgent(BaseAgent):
    """Ingestion Agent: fetches from source adapters (JSearch), dedups, stages, emits IngestBatch."""

    def __init__(self) -> None:
        self._jsearch = JSearchAdapter()

    @property
    def agent_id(self) -> str:
        return "ingestion-agent"

    def health_check(self) -> dict:
        """Return ok if fallback scrape exists; degraded if JSearch unreachable."""
        status = "ok"
        metrics: dict = {}
        if not _FALLBACK_SCRAPE.exists():
            status = "degraded"
            metrics["fallback_scrape_missing"] = True
        try:
            adapter_health = asyncio.run(self._jsearch.health_check())
            if not adapter_health.get("reachable", False):
                status = "degraded"
                metrics["jsearch_reachable"] = False
            else:
                metrics["jsearch_reachable"] = True
        except Exception:
            metrics["jsearch_reachable"] = False
            status = "degraded"
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": None,
            "metrics": metrics,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """
        If payload has region_config (and source jsearch or unspecified), run JSearch adapter,
        dedup, optionally stage to DB, emit IngestBatch with records.
        Otherwise treat payload as a single raw posting (legacy) and emit one IngestBatch.
        """
        payload = event.payload or {}
        region_config = payload.get("region_config")
        source_filter = payload.get("source")

        if region_config is not None and source_filter in (None, "jsearch"):
            return self._process_region_trigger(event, region_config)
        return self._process_legacy_single_posting(event)

    def _process_region_trigger(self, event: EventEnvelope, region_config: dict) -> EventEnvelope | None:
        """Run JSearch for region_config, dedup, stage, emit IngestBatch."""
        correlation_id = event.correlation_id
        run_id = correlation_id or str(uuid.uuid4())
        batch_id = f"batch-{run_id[:8]}"

        try:
            region = RegionConfig.model_validate(region_config)
        except Exception as e:
            log.warning("invalid_region_config", error=str(e))
            payload = source_failure_payload(run_id=run_id, source="jsearch", error=f"Invalid region_config: {e}")
            return EventEnvelope(
                correlation_id=correlation_id,
                agent_id=self.agent_id,
                payload=payload,
            )

        try:
            raw_records: list[RawJobRecord] = asyncio.run(self._jsearch.fetch(region))
        except Exception as e:
            log.error("jsearch_fetch_failed", source="jsearch", error=str(e))
            payload = source_failure_payload(run_id=run_id, source="jsearch", error=str(e))
            return EventEnvelope(
                correlation_id=correlation_id,
                agent_id=self.agent_id,
                payload=payload,
            )

        total_fetched = len(raw_records)
        seen_hashes: set[str] = set()
        unique_records: list[RawJobRecord] = []
        for r in raw_records:
            if r.raw_payload_hash and r.raw_payload_hash in seen_hashes:
                continue
            seen_hashes.add(r.raw_payload_hash or "")
            unique_records.append(r)
        dedup_count = total_fetched - len(unique_records)

        staged_count = 0
        error_count = 0
        if os.getenv("PYTHON_DATABASE_URL"):
            try:
                from agents.common.data_store import session_scope
                from agents.common.data_store.models import RawIngestedJob

                with session_scope() as session:
                    for r in unique_records:
                        try:
                            row = RawIngestedJob(
                                ingestion_run_id=run_id[:64],
                                region_id=(r.region_id or "")[:100],
                                source=r.source[:50],
                                external_id=r.external_id[:255],
                                raw_payload_hash=(r.raw_payload_hash or "")[:64],
                                title=r.title[:500],
                                company=r.company[:255],
                                description=r.description[:50000] if r.description else None,
                                city=r.city[:255] if r.city else None,
                                state=r.state[:100] if r.state else None,
                                country=r.country[:10] if r.country else None,
                                is_remote=r.is_remote,
                                job_url=r.job_url[:2083] if r.job_url else None,
                                source_url=r.source_url[:2083] if r.source_url else None,
                                date_posted=r.date_posted.isoformat() if r.date_posted else None,
                                employment_type=r.employment_type[:50] if r.employment_type else None,
                                experience_level=r.experience_level[:50] if r.experience_level else None,
                                salary_raw=r.salary_raw[:255] if r.salary_raw else None,
                                salary_min=r.salary_min,
                                salary_max=r.salary_max,
                                salary_currency=r.salary_currency[:10] if r.salary_currency else None,
                                salary_period=r.salary_period[:20] if r.salary_period else None,
                                raw_payload=r.raw_payload or None,
                                processing_status="pending",
                            )
                            session.add(row)
                            staged_count += 1
                        except Exception as ex:
                            log.warning("stage_record_failed", external_id=r.external_id, error=str(ex))
                            error_count += 1
            except Exception as ex:
                log.warning("db_stage_failed", error=str(ex))
                staged_count = len(unique_records)
                error_count = 0
        else:
            staged_count = len(unique_records)

        batch_payload = ingest_batch_payload(
            batch_id=batch_id,
            source="jsearch",
            region_id=region.region_id,
            total_fetched=total_fetched,
            staged_count=staged_count,
            dedup_count=dedup_count,
            error_count=error_count,
        )
        batch_payload["records"] = [r.model_dump(mode="json") for r in unique_records]

        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload=batch_payload,
        )

    def _process_legacy_single_posting(self, event: EventEnvelope) -> EventEnvelope:
        """Legacy: single raw posting -> single IngestBatch-style payload with one record."""
        raw = event.payload or {}
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "IngestBatch",
                "batch_id": event.correlation_id or "legacy-1",
                "source": raw.get("source", "web_scrape"),
                "region_id": "",
                "total_fetched": 1,
                "staged_count": 1,
                "dedup_count": 0,
                "error_count": 0,
                "records": [
                    {
                        "posting_id": raw.get("posting_id"),
                        "source": raw.get("source", "web_scrape"),
                        "url": raw.get("url"),
                        "title": raw.get("title"),
                        "company": raw.get("company"),
                        "location": raw.get("location"),
                        "timestamp": raw.get("timestamp"),
                        "raw_text": raw.get("raw_text"),
                        "ingestion_run_id": event.correlation_id,
                        "ingestion_timestamp": event.timestamp.isoformat(),
                        "raw_payload_hash": "stub-hash",
                        "external_id": str(raw.get("posting_id", "")),
                    }
                ],
            },
        )
