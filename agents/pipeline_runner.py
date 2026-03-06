"""
Pipeline Runner — Week 2 Walking Skeleton.

Loads 10 job postings from the fallback scrape file, runs each one through
all eight agents in sequence, and writes the full run log to:
    agents/data/output/pipeline_run.json

Usage (from the repo root):
    python agents/pipeline_runner.py

Expected output:
    pipeline_run.json  — 80 log entries (10 records x 8 agents)
    Console            — structured JSON log lines via structlog

Design decisions captured here (made during Week 2 synchronous hours):

1. SEQUENTIAL ORCHESTRATION
   One agent at a time, in fixed order.  Simple to read, simple to debug,
   easy to extend.  Adding a ninth agent means adding one line to PIPELINE.
   LangGraph StateGraph replaces this in Week 6.

2. HEALTH CHECKS FIRST
   All Phase 1 agent health checks run before any record is processed.
   If any Phase 1 agent is unhealthy, the pipeline aborts immediately.
   Phase 2 agents (demand-analysis-agent) produce a warning, not an abort.

3. CORRELATION ID
   Set once per record by the pipeline runner.  Every subsequent agent
   carries the same correlation_id unchanged.  This is how you trace a
   single job posting across all eight stages in the dashboard.

4. COMPLETE RUN LOG
   Every agent stage for every record writes one entry to pipeline_run.json,
   including Phase 2 "skipped" entries.  This gives 80 entries total and
   lets the dashboard show whether all eight stages were reached.

5. FAIL GRACEFULLY, NEVER SILENTLY
   If an agent raises an exception, the error is logged with correlation_id
   and posting_id, and the record is skipped.  The pipeline never crashes
   silently.  If 9 of 10 records succeed, those 9 are in the log.
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
#
# When run as `python agents/pipeline_runner.py` from the repo root,
# Python adds agents/ to sys.path — but our imports are `from agents.common...`
# which requires the repo root to be on the path.  This block ensures it is.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent  # repo root (parent of agents/)
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
_FALLBACK_SCRAPE = _HERE / "data" / "fixtures" / "fallback_scrape_sample.json"
_OUTPUT_DIR = _HERE / "data" / "output"
_RUN_LOG_PATH = _OUTPUT_DIR / "pipeline_run.json"

# ---------------------------------------------------------------------------
# Structured logging (structlog -> JSON to stdout)
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
# Each entry is (agent_instance, is_phase2).
# Phase 2 agents: health_check failure -> warning (not abort).
#                 process() returning None -> "phase2_skipped" log entry.

PIPELINE: list[tuple[Any, bool]] = [
    (IngestionAgent(),          False),
    (NormalizationAgent(),      False),
    (SkillsExtractionAgent(),   False),
    (EnrichmentAgent(),         False),
    (AnalyticsAgent(),          False),
    (VisualizationAgent(),      False),
    (OrchestrationAgent(),      False),
    (DemandAnalysisAgent(),     True),   # Phase 2 — expected to return None
]


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

def run_health_checks(pipeline: list[tuple[Any, bool]]) -> bool:
    """
    Run health_check() on every agent before processing any records.

    Returns True only if all Phase 1 agents are healthy.
    Phase 2 agents returning non-"ok" status log a warning and do not
    affect the return value.
    """
    all_phase1_healthy = True

    for agent, is_phase2 in pipeline:
        result = agent.health_check()
        healthy = result.get("status") == "ok"

        if healthy:
            log.info(
                "health_check_passed",
                agent_id=agent.agent_id,
                phase2=is_phase2,
                status=result.get("status"),
            )
        elif is_phase2:
            log.warning(
                "health_check_failed_phase2",
                agent_id=agent.agent_id,
                status=result.get("status"),
                note="Phase 2 agent — pipeline continues",
            )
        else:
            log.error(
                "health_check_failed",
                agent_id=agent.agent_id,
                status=result.get("status"),
                note="Phase 1 agent — pipeline will abort",
            )
            all_phase1_healthy = False

    return all_phase1_healthy


# ---------------------------------------------------------------------------
# Per-record processing
# ---------------------------------------------------------------------------

def process_record(
    raw_posting: dict,
    pipeline: list[tuple[Any, bool]],
    correlation_id: str,
) -> list[dict]:
    """
    Pass one raw posting through all eight pipeline stages.

    Returns a list of run log entries — one entry per agent.
    Phase 2 agents that return None contribute a "phase2_skipped" entry.
    If a Phase 1 agent raises an exception, the error is logged and
    processing stops for this record (no further agents run).

    The same correlation_id is carried through all stages unchanged.
    """
    run_entries: list[dict] = []

    # Initial event: raw posting wrapped in an envelope by the pipeline runner.
    current_event = EventEnvelope(
        correlation_id=correlation_id,
        agent_id="pipeline-runner",
        payload=raw_posting,
    )

    for agent, is_phase2 in pipeline:

        # --- Phase 2 stub: process() returns None ---
        if is_phase2:
            with contextlib.suppress(Exception):
                agent.process(current_event)

            # Write a "phase2_skipped" entry so the run log always has 80 rows.
            skip_entry = {
                "agent_id": agent.agent_id,
                "event_id": str(uuid.uuid4()),
                "correlation_id": correlation_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "schema_version": "1.0",
                "payload": {
                    "event_type": "Phase2Skipped",
                    "posting_id": raw_posting.get("posting_id"),
                    "note": "Phase 2 agent — not yet implemented",
                },
            }
            run_entries.append(skip_entry)
            log.warning(
                "phase2_skipped",
                agent_id=agent.agent_id,
                correlation_id=correlation_id,
                posting_id=raw_posting.get("posting_id"),
            )
            continue  # do not update current_event; phase 2 is a dead end

        # --- Phase 1 agent ---
        try:
            outbound = agent.process(current_event)
        except Exception as exc:
            log.error(
                "agent_process_error",
                agent_id=agent.agent_id,
                correlation_id=correlation_id,
                posting_id=raw_posting.get("posting_id"),
                error=str(exc),
            )
            # Stop processing this record; do not continue to later agents.
            break

        if outbound is None:
            # A Phase 1 agent should never return None, but handle it defensively.
            log.error(
                "phase1_agent_returned_none",
                agent_id=agent.agent_id,
                correlation_id=correlation_id,
                posting_id=raw_posting.get("posting_id"),
            )
            break

        # Log event to console.
        log.info(
            "event_emitted",
            agent_id=outbound.agent_id,
            event_id=outbound.event_id,
            correlation_id=outbound.correlation_id,
            timestamp=outbound.timestamp.isoformat(),
            event_type=outbound.payload.get("event_type"),
            posting_id=outbound.payload.get(
                "posting_id",
                outbound.payload.get("triggered_by_posting_id"),
            ),
        )

        # Append to run log.
        run_entries.append({
            "agent_id": outbound.agent_id,
            "event_id": outbound.event_id,
            "correlation_id": outbound.correlation_id,
            "timestamp": outbound.timestamp.isoformat(),
            "schema_version": outbound.schema_version,
            "payload": outbound.payload,
        })

        # The outbound event becomes the inbound event for the next agent.
        current_event = outbound

    return run_entries


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    1. Load postings from fallback_scrape_sample.json.
    2. Build pipeline and run health checks.
    3. Process each posting through all eight agents in sequence.
    4. Write pipeline_run.json.
    """
    run_start = datetime.now(UTC)
    run_id = str(uuid.uuid4())[:8]

    log.info(
        "pipeline_start",
        run_id=run_id,
        run_start=run_start.isoformat(),
        source=str(_FALLBACK_SCRAPE),
    )

    # Load postings.
    if not _FALLBACK_SCRAPE.exists():
        log.error("fallback_scrape_missing", path=str(_FALLBACK_SCRAPE))
        sys.exit(1)

    postings: list[dict] = json.loads(_FALLBACK_SCRAPE.read_text(encoding="utf-8"))
    log.info("postings_loaded", count=len(postings))

    # Health checks — abort if any Phase 1 agent fails.
    if not run_health_checks(PIPELINE):
        log.error(
            "pipeline_aborted",
            reason="one or more Phase 1 agents failed health_check()",
        )
        sys.exit(1)

    log.info("health_checks_passed", note="all Phase 1 agents healthy — starting run")

    # Process each posting.
    all_run_entries: list[dict] = []
    records_completed = 0

    for posting in postings:
        # Use the posting_id as correlation_id for easy cross-referencing in the dashboard.
        correlation_id = str(posting.get("posting_id"))

        log.info(
            "record_start",
            posting_id=posting.get("posting_id"),
            title=posting.get("title"),
            company=posting.get("company"),
            correlation_id=correlation_id,
        )

        entries = process_record(posting, PIPELINE, correlation_id)
        all_run_entries.extend(entries)
        records_completed += 1

        log.info(
            "record_complete",
            posting_id=posting.get("posting_id"),
            correlation_id=correlation_id,
            stages_logged=len(entries),
            expected_stages=len(PIPELINE),
        )

    # Write run log.
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _RUN_LOG_PATH.write_text(
        json.dumps(all_run_entries, indent=2, default=str),
        encoding="utf-8",
    )

    run_end = datetime.now(UTC)
    duration_s = round((run_end - run_start).total_seconds(), 3)
    expected_entries = len(postings) * len(PIPELINE)

    log.info(
        "pipeline_complete",
        run_id=run_id,
        records_processed=records_completed,
        total_entries=len(all_run_entries),
        expected_entries=expected_entries,
        run_log=str(_RUN_LOG_PATH),
        duration_seconds=duration_s,
    )

    log.info(
        "pipeline_summary",
        run_log=str(_RUN_LOG_PATH),
        records=f"{records_completed} / {len(postings)}",
        log_entries=f"{len(all_run_entries)} (expected: {expected_entries})",
        duration=f"{duration_s}s",
    )

    # Exit non-zero if any record failed to complete all stages.
    if len(all_run_entries) < expected_entries:
        log.warning(
            "pipeline_incomplete",
            expected=expected_entries,
            actual=len(all_run_entries),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
