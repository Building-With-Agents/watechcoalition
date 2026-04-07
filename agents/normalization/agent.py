"""
Normalization Agent — Week 3 Implementation (LangGraph).

Reads pending records from ``dbo.raw_ingested_jobs``, maps source fields to
canonical ``JobRecord`` schema via the mapper registry, cleans text, validates,
and writes to ``dbo.normalized_jobs``.

Agent ID (canonical): normalization-agent
Emits:    NormalizationComplete | NormalizationFailed
Consumes: IngestBatch
"""

from __future__ import annotations

import os
import uuid

import structlog
from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from agents.common.base_agent import AgentBase
from agents.common.data_store.database import check_db_connection, session_scope
from agents.common.data_store.models import (
    NormalizationQuarantine,
    NormalizedJob,
    RawIngestedJob,
)
from agents.common.event_envelope import EventEnvelope
from agents.common.types import RawJobRecord
from agents.normalization.events import (
    normalization_complete_payload,
    normalization_failed_payload,
)
from agents.normalization.mappers import get_mapper
from agents.normalization.state import NormalizationState

log = structlog.get_logger()


# ---------------------------------------------------------------------------
# LangGraph nodes
# ---------------------------------------------------------------------------


def initialize_run(state: NormalizationState) -> NormalizationState:
    """Set up the normalization run."""
    run_id = str(uuid.uuid4())
    log.info(
        "normalization_run_initialized",
        run_id=run_id,
        batch_id=state.get("batch_id", ""),
    )
    return {
        "run_id": run_id,
        "normalised_count": 0,
        "quarantined_count": 0,
        "error_count": 0,
        "status": "running",
        "errors": [],
    }


def fetch_pending_records(state: NormalizationState) -> NormalizationState:
    """Query the DB for raw records with processing_status='pending'.

    Supports batch-limited FIFO processing via NORM_BATCH_SIZE env var.
    When set, fetches at most N records ordered by created_at (oldest first).
    When unset or 0, fetches all pending records (legacy behavior).
    """
    ingestion_run_id = state.get("ingestion_run_id", "")
    batch_id = state.get("batch_id", "")

    if not check_db_connection():
        log.warning("normalization_no_db", batch_id=batch_id)
        return {"_pending_records": []}  # type: ignore[typeddict-unknown-key]

    batch_size = int(os.environ.get("NORM_BATCH_SIZE", "0"))

    try:
        with session_scope() as session:
            query = session.query(RawIngestedJob).filter(
                RawIngestedJob.processing_status == "pending",
            )
            if ingestion_run_id:
                query = query.filter(RawIngestedJob.ingestion_run_id == ingestion_run_id)

            query = query.order_by(RawIngestedJob.created_at.asc())
            if batch_size > 0:
                query = query.limit(batch_size)

            raw_rows = query.all()

            # Store row data as serializable dicts keyed by DB id
            records_data = []
            for r in raw_rows:
                records_data.append(
                    {
                        "db_id": r.id,
                        "ingestion_run_id": r.ingestion_run_id,
                        "region_id": r.region_id or "",
                        "source": r.source,
                        "external_id": r.external_id,
                        "raw_payload_hash": r.raw_payload_hash,
                        "title": r.title,
                        "company": r.company,
                        "description": r.description,
                        "city": r.city,
                        "state": r.state,
                        "country": r.country,
                        "zip_code": r.zip_code,
                        "is_remote": r.is_remote,
                        "job_url": r.job_url,
                        "source_url": r.source_url,
                        "date_posted": str(r.date_posted) if r.date_posted else None,
                        "employment_type": r.employment_type,
                        "experience_level": r.experience_level,
                        "salary_raw": r.salary_raw,
                        "salary_min": r.salary_min,
                        "salary_max": r.salary_max,
                        "salary_currency": r.salary_currency,
                        "salary_period": r.salary_period,
                        "raw_payload": r.raw_payload or {},
                    }
                )

        log.info("normalization_fetched_pending", count=len(records_data), batch_id=batch_id)
        # Stash in state as a generic dict list (TypedDict doesn't restrict extra keys)
        return {"_pending_records": records_data}  # type: ignore[typeddict-unknown-key]

    except Exception as exc:
        log.error("normalization_fetch_failed", batch_id=batch_id, error=str(exc))
        return {
            "status": "failed",
            "errors": [str(exc)],
            "_pending_records": [],  # type: ignore[typeddict-unknown-key]
        }


def check_records_available(state: NormalizationState) -> str:
    """Route: any records to normalize?"""
    records = state.get("_pending_records", [])  # type: ignore[typeddict-item]
    if not records or state.get("status") == "failed":
        return "finalize_run"
    return "normalize_records"


def normalize_records(state: NormalizationState) -> NormalizationState:
    """Apply source-specific mapper + validation to each pending record."""
    records = state.get("_pending_records", [])  # type: ignore[typeddict-item]
    ingestion_run_id = state.get("ingestion_run_id", "")

    normalised_count = 0
    quarantined_count = 0

    with session_scope() as session:
        for raw_dict in records:
            db_id = raw_dict.get("db_id")
            source = raw_dict.get("source", "")

            try:
                # Build a RawJobRecord from the DB row data
                raw_record = RawJobRecord(
                    external_id=raw_dict.get("external_id", ""),
                    source=source,
                    region_id=raw_dict.get("region_id", ""),
                    raw_payload_hash=raw_dict.get("raw_payload_hash", ""),
                    title=raw_dict.get("title", ""),
                    company=raw_dict.get("company", ""),
                    description=raw_dict.get("description") or "",
                    city=raw_dict.get("city"),
                    state=raw_dict.get("state"),
                    country=raw_dict.get("country"),
                    zip_code=raw_dict.get("zip_code"),
                    is_remote=raw_dict.get("is_remote"),
                    date_posted=raw_dict.get("date_posted"),
                    job_url=raw_dict.get("job_url"),
                    source_url=raw_dict.get("source_url") or "",
                    employment_type=raw_dict.get("employment_type"),
                    experience_level=raw_dict.get("experience_level"),
                    salary_raw=raw_dict.get("salary_raw"),
                    salary_min=raw_dict.get("salary_min"),
                    salary_max=raw_dict.get("salary_max"),
                    salary_currency=raw_dict.get("salary_currency"),
                    salary_period=raw_dict.get("salary_period"),
                    raw_payload=raw_dict.get("raw_payload") or {},
                )

                # Look up mapper from registry
                mapper = get_mapper(source)
                if mapper is None:
                    mapper = get_mapper("crawl4ai")  # fallback

                # Map raw → JobRecord (mapper applies cleaners internally)
                job_record = mapper.map(raw_record)

                # Write to normalized_jobs
                row = NormalizedJob(
                    raw_job_id=db_id,
                    ingestion_run_id=raw_dict.get("ingestion_run_id", ingestion_run_id),
                    region_id=raw_dict.get("region_id"),
                    source=job_record.source,
                    external_id=job_record.external_id,
                    title=job_record.title,
                    company=job_record.company,
                    description=job_record.description,
                    city=job_record.city,
                    state_province=job_record.state_province,
                    country=job_record.country,
                    zip_code=job_record.zip_code,
                    work_arrangement=job_record.work_arrangement,
                    is_remote=job_record.is_remote,
                    job_url=job_record.job_url,
                    employment_type=job_record.employment_type,
                    experience_level=job_record.experience_level,
                    occupation_code=job_record.occupation_code,
                    mapper_used=job_record.mapper_used,
                    date_posted=job_record.date_posted,
                    salary_raw=job_record.salary_raw,
                    salary_min=job_record.salary_min,
                    salary_max=job_record.salary_max,
                    salary_currency=job_record.salary_currency,
                    salary_period=job_record.salary_period,
                    normalization_status="success",
                )
                session.add(row)

                # Update raw record status
                raw_row = session.query(RawIngestedJob).get(db_id)
                if raw_row:
                    raw_row.processing_status = "normalized"

                normalised_count += 1

            except (ValidationError, ValueError, Exception) as exc:
                quarantined_count += 1
                log.warning(
                    "normalization_quarantine",
                    external_id=raw_dict.get("external_id"),
                    source=source,
                    error=str(exc),
                )

                # Write quarantine record
                q_row = NormalizationQuarantine(
                    raw_job_id=db_id,
                    ingestion_run_id=raw_dict.get("ingestion_run_id", ingestion_run_id),
                    source=source,
                    external_id=raw_dict.get("external_id"),
                    error_type=type(exc).__name__,
                    error_detail=str(exc),
                )
                session.add(q_row)

                # Update raw record status
                raw_row = session.query(RawIngestedJob).get(db_id)
                if raw_row:
                    raw_row.processing_status = "quarantined"

    return {
        "normalised_count": normalised_count,
        "quarantined_count": quarantined_count,
    }


def emit_normalization_complete(state: NormalizationState) -> NormalizationState:
    """Build the NormalizationComplete event payload."""
    normalised = state.get("normalised_count", 0)
    quarantined = state.get("quarantined_count", 0)

    if normalised == 0 and quarantined > 0:
        norm_status = "failed"
    elif quarantined > 0:
        norm_status = "partial"
    else:
        norm_status = "success"

    payload = normalization_complete_payload(
        batch_id=state.get("batch_id", ""),
        region_id=state.get("region_id", ""),
        normalized_count=normalised,
        quarantined_count=quarantined,
        normalization_status=norm_status,
    )
    return {"normalization_complete_event": payload}


def finalize_run(state: NormalizationState) -> NormalizationState:
    """Log completion."""
    log.info(
        "normalization_complete",
        batch_id=state.get("batch_id", ""),
        normalised_count=state.get("normalised_count", 0),
        quarantined_count=state.get("quarantined_count", 0),
    )

    # If no event was built (e.g. no records), build a minimal one
    if not state.get("normalization_complete_event"):
        errors = state.get("errors", [])
        if errors:
            payload = normalization_failed_payload(
                batch_id=state.get("batch_id", ""),
                error="; ".join(errors),
            )
        else:
            payload = normalization_complete_payload(
                batch_id=state.get("batch_id", ""),
                region_id=state.get("region_id", ""),
                normalized_count=0,
                quarantined_count=0,
                normalization_status="success",
            )
        return {"normalization_complete_event": payload, "status": "completed"}

    return {"status": "completed"}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------


def _build_graph() -> StateGraph:
    """Assemble the Normalization Agent LangGraph."""
    graph = StateGraph(NormalizationState)

    graph.add_node("initialize_run", initialize_run)
    graph.add_node("fetch_pending_records", fetch_pending_records)
    graph.add_node("normalize_records", normalize_records)
    graph.add_node("emit_normalization_complete", emit_normalization_complete)
    graph.add_node("finalize_run", finalize_run)

    graph.set_entry_point("initialize_run")
    graph.add_edge("initialize_run", "fetch_pending_records")
    graph.add_conditional_edges(
        "fetch_pending_records",
        check_records_available,
        {
            "finalize_run": "finalize_run",
            "normalize_records": "normalize_records",
        },
    )
    graph.add_edge("normalize_records", "emit_normalization_complete")
    graph.add_edge("emit_normalization_complete", "finalize_run")
    graph.add_edge("finalize_run", END)

    return graph


_COMPILED_GRAPH = _build_graph().compile()


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------


class NormalizationAgent(AgentBase):
    """Normalizes raw ingested job records into canonical JobRecord format.

    Internally powered by a LangGraph state machine.
    """

    @property
    def agent_id(self) -> str:
        return "normalization-agent"

    def health_check(self) -> dict:
        """Check DB connectivity and mapper availability."""
        from agents.normalization.mappers import MAPPER_REGISTRY

        db_ok = check_db_connection()
        return {
            "status": "ok" if db_ok else "degraded",
            "agent": self.agent_id,
            "last_run": None,
            "metrics": {},
            "db_reachable": db_ok,
            "mappers_registered": list(MAPPER_REGISTRY.keys()),
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Run the normalization graph and return the result event."""
        from contextlib import nullcontext

        from agents.common.llm_adapter import get_tracer

        payload = event.payload
        batch_id = payload.get("batch_id", "")
        ingestion_run_id = payload.get("batch_id", "")  # batch_id == run_id from ingestion
        region_id = payload.get("region_id", "")

        import json as _json

        tracer = get_tracer()

        # Serialize input EventEnvelope for Langfuse trace visibility
        _input_str: str | None = None
        if tracer:
            try:
                _input_str = _json.dumps({
                    "event_type": payload.get("event_type", "ProcessingTrigger"),
                    "correlation_id": event.correlation_id,
                    "agent_id": event.agent_id,
                    "batch_id": batch_id,
                    "region_id": region_id,
                })
            except Exception:
                pass

        span_ctx = (
            tracer.start_span(
                "normalization",
                correlation_id=event.correlation_id,
                input=_input_str,
                metadata={"batch_id": batch_id, "region_id": region_id},
            )
            if tracer
            else nullcontext()
        )

        with span_ctx:
            initial_state: NormalizationState = {
                "ingestion_run_id": ingestion_run_id,
                "correlation_id": event.correlation_id,
                "batch_id": batch_id,
                "region_id": region_id,
            }

            result = _COMPILED_GRAPH.invoke(initial_state)

            out_payload = result.get(
                "normalization_complete_event",
                {
                    "event_type": "NormalizationComplete",
                    "batch_id": batch_id,
                    "normalized_count": 0,
                    "quarantined_count": 0,
                    "normalization_status": "success",
                },
            )

            if tracer:
                try:
                    normalized = out_payload.get("normalized_count", 0)
                    quarantined = out_payload.get("quarantined_count", 0)
                    total = normalized + quarantined
                    # Log output EventEnvelope so it appears in Langfuse Output tab
                    tracer.log_event("normalization_complete", {
                        "output": _json.dumps(out_payload),
                        "normalized_count": normalized,
                        "quarantined_count": quarantined,
                        "quarantine_rate": round(quarantined / total, 4) if total > 0 else 0.0,
                    })
                except Exception:
                    pass

            return EventEnvelope(
                correlation_id=event.correlation_id,
                agent_id=self.agent_id,
                payload=out_payload,
            )
