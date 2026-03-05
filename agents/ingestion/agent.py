"""
Ingestion Agent — Week 3 Implementation (LangGraph).

Fetches job postings from configured source adapters, deduplicates, stages in
``dbo.raw_ingested_jobs``, and emits an ``IngestBatch`` event.

Agent ID (canonical): ingestion-agent
Emits:    IngestBatch | SourceFailure
Consumes: trigger event with ``region_config`` dict

CLI usage (from repo root):
    python -m agents.ingestion.agent --source crawl4ai --limit 10 --migrate
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import structlog
from langgraph.graph import END, StateGraph

from agents.common.base_agent import AgentBase
from agents.common.data_store.database import check_db_connection, session_scope
from agents.common.data_store.models import (
    JobIngestionRun,
    RawIngestedJob,
)
from agents.common.event_envelope import EventEnvelope
from agents.common.types import RawJobRecord, RegionConfig
from agents.ingestion.deduplicator import deduplicate_batch
from agents.ingestion.events import ingest_batch_payload, source_failure_payload
from agents.ingestion.sources import ADAPTER_REGISTRY, SourceAdapter, get_adapter
from agents.ingestion.state import IngestionState, SourceResult

log = structlog.get_logger()

_DEAD_LETTER_DIR = Path(__file__).parent.parent / "data" / "dead_letter"


# ---------------------------------------------------------------------------
# LangGraph nodes
# ---------------------------------------------------------------------------


def initialize_run(state: IngestionState) -> IngestionState:
    """Create the run tracking record in the DB."""
    run_id = state.get("run_id", str(uuid.uuid4()))
    region_cfg = state.get("region_config", {})
    region_id = region_cfg.get("region_id", "")
    source = region_cfg.get("sources", ["crawl4ai_indeed"])[0] if region_cfg.get("sources") else "crawl4ai_indeed"

    with session_scope() as session:
        run_record = JobIngestionRun(
            run_id=run_id,
            region_id=region_id,
            source=source,
            status="running",
        )
        session.add(run_record)

    log.info("ingestion_run_initialized", run_id=run_id, region_id=region_id)
    return {
        "run_id": run_id,
        "status": "running",
        "fetched_records": [],
        "source_results": [],
        "staged_count": 0,
        "dedup_count": 0,
        "error_count": 0,
        "errors": [],
    }


async def _fetch_all_sources(
    sources: list[str], region: RegionConfig
) -> tuple[list[RawJobRecord], list[SourceResult], list[str]]:
    """Fetch from all source adapters in parallel via asyncio.gather."""
    adapters: list[tuple[str, SourceAdapter]] = []
    for name in sources:
        try:
            adapters.append((name, get_adapter(name)))
        except ValueError as exc:
            log.warning("adapter_not_found", source=name, error=str(exc))

    if not adapters:
        return [], [], [f"No valid adapters for sources: {sources}"]

    # Launch all fetches concurrently
    tasks = [adapter.fetch(region) for _, adapter in adapters]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_records: list[RawJobRecord] = []
    source_results: list[SourceResult] = []
    errors: list[str] = []

    for (name, _adapter), result in zip(adapters, results):
        if isinstance(result, BaseException):
            err_msg = f"{name}: {result}"
            errors.append(err_msg)
            source_results.append(SourceResult(
                source_name=name,
                records_fetched=0,
                error=str(result),
            ))
            log.warning("source_fetch_failed", source=name, error=str(result))
        else:
            all_records.extend(result)
            source_results.append(SourceResult(
                source_name=name,
                records_fetched=len(result),
            ))
            log.info("source_fetch_ok", source=name, count=len(result))

    return all_records, source_results, errors


def fetch_sources(state: IngestionState) -> IngestionState:
    """Fetch records from all configured source adapters in parallel."""
    region_cfg = state.get("region_config", {})
    sources = region_cfg.get("sources", ["crawl4ai_indeed"])

    try:
        region = RegionConfig(**region_cfg)
    except Exception:
        region = RegionConfig(
            region_id=region_cfg.get("region_id", "default"),
            display_name=region_cfg.get("display_name", "Default"),
            query_location=region_cfg.get("query_location", region_cfg.get("location", "Washington state")),
            radius_miles=region_cfg.get("radius_miles", 50),
            states=region_cfg.get("states", ["WA"]),
            countries=region_cfg.get("countries", ["US"]),
            sources=sources,
            role_categories=region_cfg.get("role_categories", []),
            keywords=region_cfg.get("keywords", [region_cfg.get("query", "software engineer")]),
        )

    all_records, source_results, errors = asyncio.run(
        _fetch_all_sources(sources, region)
    )

    return {
        "fetched_records": all_records,
        "source_results": source_results,
        "errors": state.get("errors", []) + errors,
    }


def check_fetch_results(state: IngestionState) -> str:
    """Route: did we get any records?"""
    fetched = state.get("fetched_records", [])
    source_results = state.get("source_results", [])
    all_failed = all(r.error is not None for r in source_results) if source_results else True

    if not fetched and all_failed:
        return "handle_total_failure"
    return "deduplicate"


def handle_total_failure(state: IngestionState) -> IngestionState:
    """All sources failed — mark run as failed."""
    run_id = state.get("run_id", "")
    errors = state.get("errors", [])

    _update_run(run_id, status="failed", error_message="; ".join(errors))

    return {
        "status": "failed",
        "ingest_batch_event": source_failure_payload(
            run_id=run_id,
            source="all",
            error="; ".join(errors),
        ),
    }


def deduplicate(state: IngestionState) -> IngestionState:
    """Run two-phase deduplication on fetched records."""
    fetched = state.get("fetched_records", [])

    # Convert RawJobRecord objects to dicts for the deduplicator
    record_dicts = [r.model_dump() for r in fetched]

    with session_scope() as session:
        dedup_result = deduplicate_batch(record_dicts, session)

    return {
        "fetched_records": [RawJobRecord(**r) for r in dedup_result.new_records],
        "dedup_count": dedup_result.duplicates_skipped,
    }


def stage_records(state: IngestionState) -> IngestionState:
    """Write deduplicated records to the staging table."""
    run_id = state.get("run_id", "")
    records = state.get("fetched_records", [])
    region_cfg = state.get("region_config", {})
    region_id = region_cfg.get("region_id", "")

    staged_count = 0
    error_count = 0

    with session_scope() as session:
        for record in records:
            try:
                row = RawIngestedJob(
                    ingestion_run_id=run_id,
                    region_id=region_id,
                    source=record.source,
                    external_id=record.external_id,
                    raw_payload_hash=record.raw_payload_hash,
                    title=record.title,
                    company=record.company,
                    description=record.description or None,
                    city=record.city,
                    state=record.state,
                    country=record.country,
                    is_remote=record.is_remote,
                    job_url=record.job_url,
                    source_url=record.source_url or None,
                    date_posted=str(record.date_posted) if record.date_posted else None,
                    employment_type=record.employment_type,
                    experience_level=record.experience_level,
                    salary_raw=record.salary_raw,
                    salary_min=record.salary_min,
                    salary_max=record.salary_max,
                    salary_currency=record.salary_currency,
                    salary_period=record.salary_period,
                    raw_payload=record.raw_payload,
                    processing_status="pending",
                )
                session.add(row)
                session.flush()
                staged_count += 1
            except Exception as exc:
                error_count += 1
                log.warning(
                    "stage_record_failed",
                    external_id=record.external_id,
                    error=str(exc),
                )
                _quarantine_to_file(run_id, record.model_dump(), str(exc))

    return {"staged_count": staged_count, "error_count": error_count}


def emit_ingest_batch(state: IngestionState) -> IngestionState:
    """Build the IngestBatch event payload."""
    region_cfg = state.get("region_config", {})
    source_names = region_cfg.get("sources", ["crawl4ai_indeed"])
    source_label = ",".join(source_names) if len(source_names) > 1 else source_names[0]

    original_fetched = sum(
        r.records_fetched for r in state.get("source_results", [])
    )

    payload = ingest_batch_payload(
        batch_id=state.get("run_id", ""),
        source=source_label,
        region_id=region_cfg.get("region_id", ""),
        total_fetched=original_fetched,
        staged_count=state.get("staged_count", 0),
        dedup_count=state.get("dedup_count", 0),
        error_count=state.get("error_count", 0),
    )
    return {"ingest_batch_event": payload}


def finalize_run(state: IngestionState) -> IngestionState:
    """Update the run record with final counts."""
    run_id = state.get("run_id", "")
    status = state.get("status", "completed")

    original_fetched = sum(
        r.records_fetched for r in state.get("source_results", [])
    )

    _update_run(
        run_id,
        status=status if status == "failed" else "completed",
        total_fetched=original_fetched,
        staged_count=state.get("staged_count", 0),
        dedup_count=state.get("dedup_count", 0),
        error_count=state.get("error_count", 0),
    )

    log.info(
        "ingestion_complete",
        run_id=run_id,
        total_fetched=original_fetched,
        staged_count=state.get("staged_count", 0),
        dedup_count=state.get("dedup_count", 0),
        error_count=state.get("error_count", 0),
    )
    return {"status": status if status == "failed" else "completed"}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------


def _build_graph() -> StateGraph:
    """Assemble the Ingestion Agent LangGraph."""
    graph = StateGraph(IngestionState)

    graph.add_node("initialize_run", initialize_run)
    graph.add_node("fetch_sources", fetch_sources)
    graph.add_node("handle_total_failure", handle_total_failure)
    graph.add_node("deduplicate", deduplicate)
    graph.add_node("stage_records", stage_records)
    graph.add_node("emit_ingest_batch", emit_ingest_batch)
    graph.add_node("finalize_run", finalize_run)

    graph.set_entry_point("initialize_run")
    graph.add_edge("initialize_run", "fetch_sources")
    graph.add_conditional_edges(
        "fetch_sources",
        check_fetch_results,
        {
            "handle_total_failure": "handle_total_failure",
            "deduplicate": "deduplicate",
        },
    )
    graph.add_edge("handle_total_failure", "finalize_run")
    graph.add_edge("deduplicate", "stage_records")
    graph.add_edge("stage_records", "emit_ingest_batch")
    graph.add_edge("emit_ingest_batch", "finalize_run")
    graph.add_edge("finalize_run", END)

    return graph


_COMPILED_GRAPH = _build_graph().compile()


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------


class IngestionAgent(AgentBase):
    """Fetches, deduplicates, and stages job postings from external sources.

    Internally powered by a LangGraph state machine.
    """

    def __init__(self) -> None:
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict = {}

    @property
    def agent_id(self) -> str:
        return "ingestion-agent"

    def _get_last_run(self) -> dict | None:
        """Return last run info from instance state or DB."""
        if self._last_run_at is not None:
            return {
                "timestamp": self._last_run_at.isoformat(),
                "metrics": self._last_run_metrics,
            }
        # Fall back to DB query for most recent completed run
        try:
            with session_scope() as session:
                row = (
                    session.query(JobIngestionRun)
                    .filter(JobIngestionRun.status.in_(["completed", "completed_with_errors"]))
                    .order_by(JobIngestionRun.completed_at.desc())
                    .first()
                )
                if row and row.completed_at:
                    return {
                        "timestamp": row.completed_at.isoformat(),
                        "metrics": {
                            "total_fetched": row.total_fetched,
                            "staged_count": row.staged_count,
                            "dedup_count": row.dedup_count,
                            "error_count": row.error_count,
                        },
                    }
        except Exception:
            pass
        return None

    def health_check(self) -> dict:
        """Check DB connectivity and source adapter availability."""
        db_ok = check_db_connection()

        # Build per-source availability dict
        sources: dict[str, bool] = {}
        for key in ADAPTER_REGISTRY:
            try:
                adapter = get_adapter(key)
                sources[key] = adapter is not None
            except Exception:
                sources[key] = False

        if db_ok:
            status = "ok"
        else:
            status = "degraded"

        return {
            "status": status,
            "agent": self.agent_id,
            "db_reachable": db_ok,
            "sources": sources,
            "last_run": self._get_last_run(),
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Run the ingestion graph and return the result event."""
        payload = event.payload
        run_id = str(uuid.uuid4())

        # Build region_config from payload
        region_config = payload.get("region_config")
        if region_config is None:
            region_config = {
                "region_id": "default",
                "display_name": "Default Region",
                "query_location": payload.get("location", "Washington state"),
                "radius_miles": 50,
                "states": ["WA"],
                "countries": ["US"],
                "sources": payload.get("sources", ["jsearch", "crawl4ai_indeed", "crawl4ai_usajobs"]),
                "role_categories": payload.get("role_categories", []),
                "keywords": [payload.get("query", "software engineer")],
            }

        initial_state: IngestionState = {
            "run_id": run_id,
            "region_config": region_config,
            "correlation_id": event.correlation_id,
            "batch_id": run_id,
        }

        result = _COMPILED_GRAPH.invoke(initial_state)

        result_payload = result.get("ingest_batch_event", {
            "event_type": "IngestBatch",
            "batch_id": run_id,
            "total_fetched": 0,
            "staged_count": 0,
        })

        # Update instance-level last_run tracking
        self._last_run_at = datetime.now(UTC)
        self._last_run_metrics = {
            "total_fetched": result_payload.get("total_fetched", 0),
            "staged_count": result_payload.get("staged_count", 0),
            "dedup_count": result_payload.get("dedup_count", 0),
            "error_count": result_payload.get("error_count", 0),
        }

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=result_payload,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _update_run(run_id: str, *, status: str, **kwargs: object) -> None:
    """Update the run tracking record."""
    try:
        with session_scope() as session:
            run = session.query(JobIngestionRun).filter_by(run_id=run_id).first()
            if run:
                run.status = status
                run.completed_at = datetime.now(UTC)
                for key, value in kwargs.items():
                    if hasattr(run, key):
                        setattr(run, key, value)
    except Exception as exc:
        log.warning("run_update_failed", run_id=run_id, error=str(exc))


def _quarantine_to_file(run_id: str, record: dict, error: str) -> None:
    """Write a failed record to the dead letter directory."""
    _DEAD_LETTER_DIR.mkdir(parents=True, exist_ok=True)
    external_id = record.get("external_id", "unknown")
    path = _DEAD_LETTER_DIR / f"{run_id}_{external_id}.json"
    try:
        path.write_text(
            json.dumps({"record": record, "error": error, "run_id": run_id}, indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as exc:
        log.warning("dead_letter_write_failed", path=str(path), error=str(exc))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _cli() -> None:
    """CLI for running the Ingestion Agent standalone."""
    import argparse

    parser = argparse.ArgumentParser(description="Run the Ingestion Agent")
    all_sources = ["jsearch", "crawl4ai_indeed", "crawl4ai_usajobs"]

    parser.add_argument(
        "--sources", nargs="+",
        choices=all_sources,
        default=all_sources,
        help="Source adapters to fetch from",
    )
    parser.add_argument("--query", default="software engineer")
    parser.add_argument("--location", default="Washington state")
    parser.add_argument("--migrate", action="store_true", help="Run DB migrations before ingestion")
    args = parser.parse_args()

    if args.migrate:
        from agents.common.data_store.database import get_engine
        from agents.common.data_store.migrations import run_migrations
        run_migrations(get_engine())

    agent = IngestionAgent()

    health = agent.health_check()
    log.info("health_check", **health)

    trigger = EventEnvelope(
        correlation_id=str(uuid.uuid4()),
        agent_id="cli",
        payload={
            "sources": args.sources,
            "query": args.query,
            "location": args.location,
        },
    )

    result = agent.process(trigger)
    log.info("ingestion_result", **result.payload)


if __name__ == "__main__":
    _cli()
