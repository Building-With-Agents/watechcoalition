"""
Pipeline Runner — Week 3 Batch-Oriented.

Sends a batch trigger to the Ingestion Agent, which fetches its own data.
The Normalization Agent reads staged records from the DB.
Downstream agents (Skills Extraction through Orchestration) are still stubs
that pass through the upstream event.

Usage (from the repo root):
    python agents/pipeline_runner.py

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

import contextlib
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import structlog  # noqa: E402

from agents.analytics.agent import AnalyticsAgent  # noqa: E402
from agents.common.event_envelope import EventEnvelope  # noqa: E402
from agents.demand_analysis.agent import DemandAnalysisAgent  # noqa: E402
from agents.enrichment.agent import EnrichmentAgent  # noqa: E402
from agents.ingestion.agent import IngestionAgent  # noqa: E402
from agents.normalization.agent import NormalizationAgent  # noqa: E402
from agents.orchestration.agent import OrchestrationAgent  # noqa: E402
from agents.skills_extraction.agent import SkillsExtractionAgent  # noqa: E402
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

# ---------------------------------------------------------------------------
# Pipeline definition
# ---------------------------------------------------------------------------

PIPELINE: list[tuple[Any, bool]] = [
    (IngestionAgent(),          False),
    (NormalizationAgent(),      False),
    (SkillsExtractionAgent(),   False),
    (EnrichmentAgent(),         False),
    (AnalyticsAgent(),          False),
    (VisualizationAgent(),      False),
    (OrchestrationAgent(),      False),
    (DemandAnalysisAgent(),     True),
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
                "timestamp": datetime.now(UTC).isoformat(),
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

        run_entries.append({
            "agent_id": outbound.agent_id,
            "event_id": outbound.event_id,
            "correlation_id": outbound.correlation_id,
            "timestamp": outbound.timestamp.isoformat(),
            "schema_version": outbound.schema_version,
            "payload": outbound.payload,
        })

        current_event = outbound

    return run_entries


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Send a batch trigger through the pipeline."""
    run_start = datetime.now(UTC)
    run_id = str(uuid.uuid4())[:8]
    correlation_id = f"pipeline-{run_id}"

    log.info("pipeline_start", run_id=run_id, run_start=run_start.isoformat())

    # Health checks
    if not run_health_checks(PIPELINE):
        log.error("pipeline_aborted", reason="Phase 1 agent health check failed")
        sys.exit(1)

    log.info("health_checks_passed", note="all Phase 1 agents healthy — starting run")

    # Batch trigger with region_config (backward-compat: old keys also accepted)
    trigger_payload = {
        "region_config": {
            "region_id": "wa-default",
            "display_name": "Washington State",
            "query_location": "Washington state",
            "radius_miles": 50,
            "states": ["WA"],
            "countries": ["US"],
            "sources": ["jsearch", "crawl4ai_indeed", "crawl4ai_usajobs"],
            "role_categories": ["Software Engineering"],
            "keywords": ["software engineer"],
        },
    }

    entries = run_pipeline(PIPELINE, correlation_id, trigger_payload)

    # Write run log
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _RUN_LOG_PATH.write_text(
        json.dumps(entries, indent=2, default=str),
        encoding="utf-8",
    )

    run_end = datetime.now(UTC)
    duration_s = round((run_end - run_start).total_seconds(), 3)

    log.info(
        "pipeline_complete",
        run_id=run_id,
        total_entries=len(entries),
        expected_entries=len(PIPELINE),
        run_log=str(_RUN_LOG_PATH),
        duration_seconds=duration_s,
    )


if __name__ == "__main__":
    main()
