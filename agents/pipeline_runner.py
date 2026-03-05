"""
Pipeline Runner — Week 2 Walking Skeleton.

Loads 10 job postings from the fallback scrape file, runs each one through
all eight agents in sequence, and writes the full run log to:
    agents/data/output/pipeline_run.json

Usage (from repo root or agents/):
    python -m agents.pipeline_runner
        Run all eight agents (80 log entries for 10 records).

    python -m agents.pipeline_runner --steps ingestion normalization
        Run from ingestion through normalization (inclusive); no agents skipped
        between. START and END are in canonical pipeline order.

    python -m agents.pipeline_runner --help
        Show usage and exit.

Commands:
    python -m agents.pipeline_runner
        Full pipeline, 80 entries (10 × 8).
    python -m agents.pipeline_runner --steps START END
        Run from START through END (inclusive); all agents between are run. No skipping.

Expected output:
    pipeline_run.json  — 80 log entries (10 records × 8 agents)
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

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import structlog

from agents.common.event_envelope import EventEnvelope

# Canonical pipeline order (execution always follows this order).
CANONICAL_AGENT_IDS = [
    "ingestion",
    "normalization",
    "skills_extraction",
    "enrichment",
    "analytics",
    "visualization",
    "orchestration",
    "demand_analysis",
]

# (agent_id, is_phase2) — Phase 2 agents produce a warning on unhealthy, not an abort.
PIPELINE = [
    ("ingestion", False),
    ("normalization", False),
    ("skills_extraction", False),
    ("enrichment", False),
    ("analytics", False),
    ("visualization", False),
    ("orchestration", False),
    ("demand_analysis", True),
]


def _agents_dir() -> Path:
    """Return the agents/ directory (parent of this file)."""
    return Path(__file__).resolve().parent


def _stub_agent(agent_id: str, health_check_fn: Any):
    """Wrap a module that only has health_check(); provide passthrough process()."""

    class StubAgent:
        def __init__(self, aid: str, hc: Any) -> None:
            self.agent_id = aid
            self._health_check = hc

        def health_check(self) -> dict:
            return self._health_check()

        def process(self, event: EventEnvelope) -> EventEnvelope:
            return EventEnvelope(
                correlation_id=event.correlation_id,
                agent_id=self.agent_id,
                payload=event.payload,
            )

    return StubAgent(agent_id, health_check_fn)


def _get_agent(agent_id: str):
    """Return an agent instance with health_check() and process(event)."""
    if agent_id == "ingestion":
        from agents.ingestion.agent import IngestionAgent
        return IngestionAgent(agent_id="ingestion")
    if agent_id == "normalization":
        from agents.normalization.agent import NormalizationAgent
        return NormalizationAgent(agent_id="normalization")
    if agent_id == "skills_extraction":
        from agents.skills_extraction.agent import SkillsExtractionAgent
        return SkillsExtractionAgent(agent_id="skills_extraction")
    if agent_id == "enrichment":
        from agents.enrichment.agent import EnrichmentAgent
        return EnrichmentAgent(agent_id="enrichment")
    if agent_id == "analytics":
        from agents.analytics.agent import AnalyticsAgent
        return AnalyticsAgent(agent_id="analytics")
    if agent_id == "visualization":
        from agents.visualization.agent import VisualizationAgent
        return VisualizationAgent(agent_id="visualization")
    if agent_id == "orchestration":
        from agents.orchestration.agent import OrchestrationAgent
        return OrchestrationAgent(agent_id="orchestration")
    if agent_id == "demand_analysis":
        from agents.demand_analysis.agent import DemandAnalysisAgent
        return DemandAnalysisAgent(agent_id="demand_analysis")
    raise ValueError(f"Unknown agent_id: {agent_id}")


def parse_args() -> list[tuple[str, bool]]:
    """Parse CLI; return list of (agent_id, is_phase2) in canonical order.
    --steps START END: run from START through END (inclusive), no agents skipped.
    """
    parser = argparse.ArgumentParser(
        description="Run the Job Intelligence Engine pipeline (all or selected steps)."
    )
    parser.add_argument(
        "--steps",
        nargs=2,
        default=None,
        metavar=("START", "END"),
        help="Run from START through END (inclusive) in canonical order. Example: --steps ingestion visualization",
    )
    args = parser.parse_args()
    if args.steps is None:
        return list(PIPELINE)
    start, end = (s.strip().lower() for s in args.steps)
    for name, label in [(start, "START"), (end, "END")]:
        if name not in CANONICAL_AGENT_IDS:
            parser.error(f"Unknown {label} step: {name}. Valid: {CANONICAL_AGENT_IDS}")
    i_start = CANONICAL_AGENT_IDS.index(start)
    i_end = CANONICAL_AGENT_IDS.index(end)
    if i_start > i_end:
        parser.error(
            f"START ({start}) must come before or equal to END ({end}) in pipeline order. Order: {CANONICAL_AGENT_IDS}"
        )
    return PIPELINE[i_start : i_end + 1]


def run_health_checks(pipeline_to_run: list[tuple[str, bool]], log: Any) -> None:
    """Run health checks for all agents in pipeline_to_run. Abort if Phase 1 unhealthy."""
    for agent_id, is_phase2 in pipeline_to_run:
        agent = _get_agent(agent_id)
        result = agent.health_check()
        status = result.get("status", "down")
        if status != "ok":
            if is_phase2:
                log.warning(
                    "phase2_agent_unhealthy",
                    agent=agent_id,
                    status=status,
                    metrics=result.get("metrics"),
                )
            else:
                log.error(
                    "phase1_agent_unhealthy_aborting",
                    agent=agent_id,
                    status=status,
                    metrics=result.get("metrics"),
                )
                sys.exit(1)


def load_postings() -> list[dict]:
    """Load job postings from the fallback scrape fixture."""
    path = _agents_dir() / "data" / "fixtures" / "fallback_scrape_sample.json"
    if not path.exists():
        raise FileNotFoundError(f"Fallback fixture not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def process_record(
    posting: dict,
    pipeline_to_run: list[tuple[str, bool]],
    run_log: list[dict],
    log: Any,
) -> None:
    """Run one record through the selected pipeline steps; append entries to run_log."""
    correlation_id = str(posting.get("posting_id", ""))
    event = EventEnvelope(
        correlation_id=correlation_id,
        agent_id="pipeline_runner",
        payload=posting,
    )
    for agent_id, _ in pipeline_to_run:
        agent = _get_agent(agent_id)
        try:
            out = agent.process(event)
            if out is None:
                run_log.append({
                    "correlation_id": correlation_id,
                    "posting_id": posting.get("posting_id"),
                    "agent_id": agent_id,
                    "status": "skipped",
                    "timestamp": event.timestamp.isoformat(),
                })
            else:
                run_log.append({
                    "correlation_id": correlation_id,
                    "posting_id": posting.get("posting_id"),
                    "agent_id": agent_id,
                    "status": "ok",
                    "timestamp": out.timestamp.isoformat(),
                })
                event = out
        except Exception as exc:
            log.exception(
                "agent_stage_failed",
                correlation_id=correlation_id,
                posting_id=posting.get("posting_id"),
                agent_id=agent_id,
                error=str(exc),
            )
            run_log.append({
                "correlation_id": correlation_id,
                "posting_id": posting.get("posting_id"),
                "agent_id": agent_id,
                "status": "failed",
                "timestamp": event.timestamp.isoformat(),
                "error": str(exc),
            })
            return


def main() -> None:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )
    log = structlog.get_logger()

    pipeline_to_run = parse_args()
    log.info("pipeline_start", steps=[a for a, _ in pipeline_to_run])

    postings = load_postings()
    log.info("postings_loaded", count=len(postings), path=str(_agents_dir() / "data" / "fixtures" / "fallback_scrape_sample.json"))

    run_health_checks(pipeline_to_run, log)

    run_log: list[dict] = []
    for posting in postings:
        process_record(posting, pipeline_to_run, run_log, log)

    out_path = _agents_dir() / "data" / "output" / "pipeline_run.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(run_log, f, indent=2)

    expected = len(postings) * len(pipeline_to_run)
    log.info(
        "pipeline_complete",
        run_log_entries=len(run_log),
        expected_entries=expected,
        output_path=str(out_path),
    )


if __name__ == "__main__":
    main()