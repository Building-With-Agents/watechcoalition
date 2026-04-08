"""
Pipeline Runner — Demo Run (Week 2 fixture data only).

DEPRECATED for production use. Use the flywheel pipeline instead:
  - Loop 1 (ingest):  python agents/scripts/batch_ingest.py
  - Loop 2 (process): python agents/scripts/run_processing_loop.py

This script runs all agents sequentially in a single pass with fixture data.
Kept for Week 2 walking skeleton demos and test_pipeline_runner.py.

Usage (from the repo root):
    python agents/pipeline_runner.py

Redis is not used. For an optional Redis Streams prototype (Phase 2 bus exploration),
see ``agents/scripts/run_full_pipeline_redis.py``.

Design decisions:

1. BATCH-ORIENTED PIPELINE
   Ingestion Agent receives a trigger event with a ``region_config`` dict
   and fetches + deduplicates + stages records itself.  The Normalization
   Agent reads pending records from the DB (processing_status='pending').

2. HEALTH CHECKS FIRST
   All Phase 1 agent health checks run before any processing.
   Phase 2 agents (demand-analysis-agent) produce a warning, not an abort.
   Health check failures for DB-dependent agents (ingestion, normalization)
   are tolerated as "degraded" — the pipeline still runs.

3. SEQUENTIAL STAGES
   One agent at a time, in fixed order.  LangGraph replaces this in Week 6.

4. COMPLETE RUN LOG
   Every agent stage writes one entry to pipeline_run.json.

5. FAIL GRACEFULLY, NEVER SILENTLY
   If an agent raises an exception, the error is logged and the pipeline
   continues with the remaining agents if possible.
"""

from __future__ import annotations

import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import contextlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402
import structlog  # noqa: E402

load_dotenv(_REPO_ROOT / ".env")

from agents.analytics.agent import AnalyticsAgent  # noqa: E402
from agents.analytics.agent import register_alert_bus as register_analytics_alert_bus  # noqa: E402
from agents.common.event_envelope import EventEnvelope  # noqa: E402
from agents.common.llm_adapter import register_tracer  # noqa: E402
from agents.common.message_bus import InProcessEventBus  # noqa: E402
from agents.common.message_bus.contracts import ORCHESTRATOR_AGENT_ID  # noqa: E402
from agents.common.observability import LangfuseTracer  # noqa: E402
from agents.common.types import JobRecord  # noqa: E402
from agents.demand_analysis.agent import DemandAnalysisAgent  # noqa: E402
from agents.enrichment.agent import (  # noqa: E402
    EnrichmentAgent,
    register_alert_bus as register_enrichment_alert_bus,
)
from agents.ingestion.agent import IngestionAgent  # noqa: E402
from agents.normalization.agent import NormalizationAgent  # noqa: E402
from agents.orchestration.agent import OrchestrationAgent  # noqa: E402
from agents.skills_extraction.agent import SkillsExtractionAgent  # noqa: E402
from agents.skills_extraction.extractors.context import extract_context  # noqa: E402
from agents.skills_extraction.extractors.responsibilities import extract_responsibilities  # noqa: E402
from agents.skills_extraction.extractors.tasks import extract_tasks  # noqa: E402
from agents.visualization.agent import VisualizationAgent  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
_OUTPUT_DIR = _HERE / "data" / "output"
_RUN_LOG_PATH = _OUTPUT_DIR / "pipeline_run.json"

# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()


def _on_enrichment_degraded_alert(event: EventEnvelope) -> None:
    """Orchestration-side receipt for EnrichmentDegraded (bus subscriber).

    Week 6: persist to orchestration_audit_log / alerts. Phase 1: structured log only.
    """
    log.warning(
        "orchestration_EnrichmentDegraded_received",
        correlation_id=event.correlation_id,
        normalized_job_id=event.payload.get("normalized_job_id"),
        posting_id=event.payload.get("posting_id"),
        reason=event.payload.get("reason"),
        classifier=event.payload.get("classifier"),
    )


def _on_emergence_alert(event: EventEnvelope) -> None:
    """Orchestration-side receipt for EmergenceAlert (bus subscriber). Phase 1: structured log only."""
    log.warning(
        "orchestration_EmergenceAlert_received",
        correlation_id=event.correlation_id,
        posting_count=event.payload.get("posting_count"),
        candidate_role_label=event.payload.get("candidate_role_label"),
        nearest_canonical_role=event.payload.get("nearest_canonical_role"),
    )


# ---------------------------------------------------------------------------
# Optional: smoke-call extractors after normalization (needs title + company)
# ---------------------------------------------------------------------------


def _job_record_from_event_payload(payload: dict) -> JobRecord | None:
    """Build a minimal JobRecord when inline job fields exist (not batch-only events)."""
    title = payload.get("title")
    company = payload.get("company")
    if not isinstance(title, str) or not title.strip():
        return None
    if not isinstance(company, str) or not company.strip():
        return None
    desc = payload.get("description") if isinstance(payload.get("description"), str) else None
    if desc is None and isinstance(payload.get("raw_text"), str):
        desc = payload["raw_text"]
    req = payload.get("requirements") if isinstance(payload.get("requirements"), str) else None
    resp = payload.get("responsibilities") if isinstance(payload.get("responsibilities"), str) else None
    return JobRecord(
        source=str(payload.get("source") or "pipeline-runner"),
        external_id=str(payload.get("external_id") or payload.get("batch_id") or "pipeline-stub"),
        title=title.strip(),
        company=company.strip(),
        description=desc,
        requirements=req,
        responsibilities=resp,
    )


# ---------------------------------------------------------------------------
# Pipeline definition
# ---------------------------------------------------------------------------

PIPELINE: list[tuple[Any, bool]] = [
    (IngestionAgent(), False),
    (NormalizationAgent(), False),
    (SkillsExtractionAgent(), False),
    (EnrichmentAgent(), False),
    (AnalyticsAgent(), False),
    (VisualizationAgent(), False),
    (OrchestrationAgent(), False),
    (DemandAnalysisAgent(), True),
]


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------


def run_health_checks(pipeline: list[tuple[Any, bool]]) -> bool:
    """Run health_check() on every agent.

    Returns True if all Phase 1 agents report "ok" or "degraded".
    Phase 2 agents log warnings but don't block.
    """
    all_phase1_healthy = True

    for agent, is_phase2 in pipeline:
        result = agent.health_check()
        status = result.get("status", "down")

        if status in ("ok", "degraded"):
            log.info(
                "health_check_passed",
                agent_id=agent.agent_id,
                phase2=is_phase2,
                status=status,
            )
        elif is_phase2:
            log.warning(
                "health_check_failed_phase2",
                agent_id=agent.agent_id,
                status=status,
                note="Phase 2 agent — pipeline continues",
            )
        else:
            log.error(
                "health_check_failed",
                agent_id=agent.agent_id,
                status=status,
                note="Phase 1 agent — pipeline will abort",
            )
            all_phase1_healthy = False

    return all_phase1_healthy


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------


def run_pipeline(
    pipeline: list[tuple[Any, bool]],
    correlation_id: str,
    trigger_payload: dict,
) -> list[dict]:
    """Run all pipeline stages sequentially.

    The Ingestion Agent receives the trigger_payload and fetches its own data.
    Each subsequent agent receives the output of the previous agent.

    After the normalization agent, extraction stubs (e.g. extract_context) are
    called with the outbound payload; result counts are logged via structlog
    (no PII). Stubs return empty lists and do not block the pipeline.
    """
    run_entries: list[dict] = []

    current_event = EventEnvelope(
        correlation_id=correlation_id,
        agent_id="pipeline-runner",
        payload=trigger_payload,
    )

    for agent, is_phase2 in pipeline:
        # Phase 2 stub
        if is_phase2:
            with contextlib.suppress(Exception):
                agent.process(current_event)

            skip_entry = {
                "agent_id": agent.agent_id,
                "event_id": str(uuid.uuid4()),
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0",
                "payload": {
                    "event_type": "Phase2Skipped",
                    "note": "Phase 2 agent — not yet implemented",
                },
            }
            run_entries.append(skip_entry)
            log.warning("phase2_skipped", agent_id=agent.agent_id, correlation_id=correlation_id)
            continue

        # Phase 1 agent
        try:
            outbound = agent.process(current_event)
        except Exception as exc:
            log.error(
                "agent_process_error",
                agent_id=agent.agent_id,
                correlation_id=correlation_id,
                error=str(exc),
            )
            break

        if outbound is None:
            log.error(
                "phase1_agent_returned_none",
                agent_id=agent.agent_id,
                correlation_id=correlation_id,
            )
            break

        log.info(
            "event_emitted",
            agent_id=outbound.agent_id,
            event_id=outbound.event_id,
            correlation_id=outbound.correlation_id,
            event_type=outbound.payload.get("event_type"),
        )

        # Week 5: optional extractor smoke after normalization (full run is in SkillsExtractionAgent).
        if outbound.agent_id == "normalization-agent":
            stub_rec = _job_record_from_event_payload(outbound.payload)
            if stub_rec is None:
                stub_rec = JobRecord(
                    source="pipeline-stub",
                    external_id="stub",
                    title="stub",
                    company="stub",
                )
            context_signals, _ctx_meta = extract_context(stub_rec)
            tasks, _tasks_meta = extract_tasks(stub_rec)
            responsibilities, _resp_meta = extract_responsibilities(stub_rec)
            log.info(
                "extraction_stubs_result",
                context_count=len(context_signals),
                tasks_count=len(tasks),
                responsibilities_count=len(responsibilities),
                correlation_id=outbound.correlation_id,
            )

        run_entries.append(
            {
                "agent_id": outbound.agent_id,
                "event_id": outbound.event_id,
                "correlation_id": outbound.correlation_id,
                "timestamp": outbound.timestamp.isoformat(),
                "schema_version": outbound.schema_version,
                "payload": outbound.payload,
            }
        )

        current_event = outbound

    return run_entries


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Send a batch trigger through the pipeline."""
    run_start = datetime.now(timezone.utc)
    run_id = str(uuid.uuid4())[:8]
    correlation_id = f"pipeline-{run_id}"

    log.info("pipeline_start", run_id=run_id, run_start=run_start.isoformat())

    alert_bus = InProcessEventBus()
    alert_bus.subscribe(
        "EnrichmentDegraded",
        _on_enrichment_degraded_alert,
        subscriber_id=ORCHESTRATOR_AGENT_ID,
    )
    alert_bus.subscribe(
        "EmergenceAlert",
        _on_emergence_alert,
        subscriber_id=ORCHESTRATOR_AGENT_ID,
    )
    register_enrichment_alert_bus(alert_bus)
    register_analytics_alert_bus(alert_bus)

    # Langfuse tracing (optional — activate only when API key is present)
    if os.getenv("LANGFUSE_SECRET_KEY"):
        _tracer = LangfuseTracer(agent_id="pipeline-runner")
        register_tracer(_tracer)
        log.info("langfuse_tracer_registered", agent_id="pipeline-runner")

    try:
        # Health checks
        if not run_health_checks(PIPELINE):
            log.error("pipeline_aborted", reason="Phase 1 agent health check failed")
            sys.exit(1)

        log.info("health_checks_passed", note="all Phase 1 agents healthy — starting run")

        # Batch trigger with region_config (backward-compat: old keys also accepted)
        trigger_payload = {
            "region_config": {
                "region_id": "borderplex-default",
                "display_name": "Borderplex Region",
                "query_location": "El Paso Texas",
                "radius_miles": 50,
                "states": ["TX", "NM"],
                "countries": ["US"],
                "sources": ["jsearch", "crawl4ai"],
                "role_categories": ["Software Engineering"],
                "keywords": ["software engineer"],
            },
        }

        entries = run_pipeline(PIPELINE, correlation_id, trigger_payload)

        # Write run log — TODO: migrate dashboard to read from DB instead of JSON
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        _RUN_LOG_PATH.write_text(
            json.dumps(entries, indent=2, default=str),
            encoding="utf-8",
        )

        run_end = datetime.now(timezone.utc)
        duration_s = round((run_end - run_start).total_seconds(), 3)

        log.info(
            "pipeline_complete",
            run_id=run_id,
            total_entries=len(entries),
            expected_entries=len(PIPELINE),
            run_log=str(_RUN_LOG_PATH),
            duration_seconds=duration_s,
        )
    finally:
        register_enrichment_alert_bus(None)
        register_analytics_alert_bus(None)
        # Flush and shut down Langfuse tracer so all traces are sent
        if _tracer is not None and hasattr(_tracer, "shutdown"):
            _tracer.shutdown()
            register_tracer(None)


if __name__ == "__main__":
    main()
