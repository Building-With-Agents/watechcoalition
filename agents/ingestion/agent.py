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
from datetime import datetime, timezone
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
from agents.ingestion.sources import get_adapter
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
    source = region_cfg.get("sources", ["crawl4ai"])[0] if region_cfg.get("sources") else "crawl4ai"

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


def fetch_sources(state: IngestionState) -> IngestionState:
    """Fetch records from all configured source adapters."""
    region_cfg = state.get("region_config", {})
    sources = region_cfg.get("sources", ["crawl4ai"])

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

    n = len(sources)
    per_index_records: list[list[RawJobRecord]] = [[] for _ in range(n)]
    per_index_error: list[str | None] = [None] * n
    errors: list[str] = []

    async def _gather_crawl4ai(
        indices_and_names: list[tuple[int, str]],
    ) -> list[tuple[int, str, list[RawJobRecord], Exception | None]]:
        async def fetch_one(idx: int, source_name: str) -> tuple[int, str, list[RawJobRecord], Exception | None]:
            try:
                adapter = get_adapter(source_name)
                recs = await adapter.fetch(region)
                return (idx, source_name, recs, None)
            except Exception as exc:
                log.warning("source_fetch_failed", source=source_name, error=str(exc))
                return (idx, source_name, [], exc)

        return await asyncio.gather(
            *[fetch_one(i, name) for i, name in indices_and_names],
        )

    crawl4ai_pending = [(i, sources[i]) for i in range(n) if sources[i].startswith("crawl4ai")]

    for i, source_name in enumerate(sources):
        if source_name.startswith("crawl4ai"):
            continue
        try:
            adapter = get_adapter(source_name)
            records = asyncio.run(adapter.fetch(region))
            per_index_records[i] = records
            log.info("source_fetch_ok", source=source_name, count=len(records))
        except Exception as exc:
            err_msg = f"{source_name}: {exc}"
            errors.append(err_msg)
            per_index_error[i] = str(exc)
            log.warning("source_fetch_failed", source=source_name, error=str(exc))

    if crawl4ai_pending:
        for idx, source_name, records, exc in asyncio.run(_gather_crawl4ai(crawl4ai_pending)):
            if exc is not None:
                err_msg = f"{source_name}: {exc}"
                errors.append(err_msg)
                per_index_error[idx] = str(exc)
            else:
                per_index_records[idx] = records
                log.info("source_fetch_ok", source=source_name, count=len(records))

    all_records: list[RawJobRecord] = []
    source_results: list[SourceResult] = []
    for i, source_name in enumerate(sources):
        recs = per_index_records[i]
        all_records.extend(recs)
        source_results.append(
            SourceResult(
                source_name=source_name,
                records_fetched=len(recs),
                error=per_index_error[i],
            )
        )

    # Cap total fetched records to limit (default 50) when set on state
    cap = state.get("limit")
    if isinstance(cap, int) and cap > 0 and len(all_records) > cap:
        original_count = len(all_records)
        all_records = all_records[:cap]
        log.info("ingestion_capped", limit=cap, total_before_cap=original_count, capped_to=len(all_records))
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
                    zip_code=record.zip_code,
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
    source_names = region_cfg.get("sources", ["crawl4ai"])
    source_label = ",".join(source_names) if len(source_names) > 1 else source_names[0]

    original_fetched = sum(r.records_fetched for r in state.get("source_results", []))

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

    original_fetched = sum(r.records_fetched for r in state.get("source_results", []))

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

    @property
    def agent_id(self) -> str:
        return "ingestion-agent"

    def health_check(self) -> dict:
        """Check DB connectivity and source adapter availability."""
        db_ok = check_db_connection()
        fixture_ok = (Path(__file__).parent.parent / "data" / "fixtures" / "fallback_scrape_sample.json").exists()

        if db_ok and fixture_ok:
            status = "ok"
        elif db_ok or fixture_ok:
            status = "degraded"
        else:
            status = "down"

        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": None,
            "metrics": {},
            "db_reachable": db_ok,
            "sources": {"fixture_available": fixture_ok},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Run the ingestion graph and return the result event."""
        payload = event.payload
        run_id = str(uuid.uuid4())

        # Build region_config from payload (supports both old and new format)
        region_config = payload.get("region_config")
        if region_config is None:
            # Backward compat: old-style payload with source/limit/query/location
            source = payload.get("source", "crawl4ai")
            region_config = {
                "region_id": "default",
                "display_name": "Default Region",
                "query_location": payload.get("location", "Washington state"),
                "radius_miles": 50,
                "states": ["WA"],
                "countries": ["US"],
                "sources": [source] if source != "all" else ["jsearch", "crawl4ai"],
                "role_categories": [],
                "keywords": [payload.get("query", "software engineer")],
            }
        # Cap number of jobs: from region_config, top-level payload, or default 50
        limit = 50
        if isinstance(region_config, dict) and isinstance(region_config.get("limit"), int):
            limit = region_config["limit"]
        elif isinstance(payload.get("limit"), int):
            limit = payload["limit"]

        initial_state: IngestionState = {
            "run_id": run_id,
            "region_config": region_config,
            "limit": limit,
            "correlation_id": event.correlation_id,
            "batch_id": run_id,
        }

        result = _COMPILED_GRAPH.invoke(initial_state)

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=result.get(
                "ingest_batch_event",
                {
                    "event_type": "IngestBatch",
                    "batch_id": run_id,
                    "total_fetched": 0,
                    "staged_count": 0,
                },
            ),
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
                run.completed_at = datetime.now(timezone.utc)
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

    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

    parser = argparse.ArgumentParser(description="Run the Ingestion Agent")
    parser.add_argument("--source", choices=["jsearch", "crawl4ai", "all"], default="all")
    parser.add_argument("--limit", type=int, default=50)
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
            "source": args.source,
            "limit": args.limit,
            "query": args.query,
            "location": args.location,
        },
    )

    result = agent.process(trigger)
    log.info("ingestion_result", **result.payload)


if __name__ == "__main__":
    _cli()
