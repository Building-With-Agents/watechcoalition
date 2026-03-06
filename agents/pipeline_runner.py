"""
Sequential pipeline runner for the Job Intelligence Engine (Task 2.3).

Chains all eight agents in order: runs health checks (abort if any unhealthy),
passes each raw job posting through the pipeline with a single correlation_id per
record, logs every event with structlog, and writes the full run log to
agents/data/output/pipeline_run.json. Each run overwrites that file (no append).

Run from repo root:
  python -m agents.pipeline_runner
  python -m agents.pipeline_runner --input path/to/postings.json
  python -m agents.pipeline_runner --agents 0:3   # run only first three agents (debug)

Correlation_id originates here (one per record) and is propagated unchanged by
each agent via create_outbound_event(). Extensibility: add a ninth agent by
appending to PIPELINE_AGENTS. Selectivity: use --agents 0:3 to run a prefix.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any

# Ensure repo root is on path when run as script
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import structlog

from agents.common.datetime_utils import datetime_to_iso_utc, utc_now_iso
from agents.common.event_envelope import EventEnvelope
from agents.common.paths import FALLBACK_SCRAPE_PATH, OUTPUT_DIR, PIPELINE_RUN_JSON
from agents.ingestion.agent import IngestionAgent
from agents.normalization.agent import NormalizationAgent
from agents.skills_extraction.agent import SkillsExtractionAgent
from agents.enrichment.agent import EnrichmentAgent
from agents.demand_analysis.agent import DemandAnalysisAgent
from agents.analytics.agent import AnalyticsAgent
from agents.visualization.agent import VisualizationAgent
from agents.orchestration.agent import OrchestrationAgent

log = structlog.get_logger()

# Ordered list of (display_name, agent_instance). Extensibility: add a ninth by appending.
PIPELINE_AGENTS = [
    ("ingestion", IngestionAgent()),
    ("normalization", NormalizationAgent()),
    ("skills_extraction", SkillsExtractionAgent()),
    ("enrichment", EnrichmentAgent()),
    ("demand_analysis", DemandAnalysisAgent()),
    ("analytics", AnalyticsAgent()),
    ("visualization", VisualizationAgent()),
    ("orchestration", OrchestrationAgent()),
]


def _health_check_gate() -> None:
    """Run health checks on all agents. Abort with clear message if any is unhealthy."""
    unhealthy = []
    for name, agent in PIPELINE_AGENTS:
        h = agent.health_check()
        status = h.get("status", "?")
        if status not in ("ok", "degraded"):
            unhealthy.append((name, status))
    if unhealthy:
        msg = "Pipeline aborted: unhealthy agent(s): " + ", ".join(
            f"{n}={s}" for n, s in unhealthy
        )
        log.error("health_check_failed", unhealthy=unhealthy, message=msg)
        raise SystemExit(msg)


def _event_to_log_dict(ev: EventEnvelope) -> dict[str, Any]:
    """Required structlog fields per event: agent_id, event_id, correlation_id, timestamp."""
    return {
        "agent_id": ev.agent_id,
        "event_id": ev.event_id,
        "correlation_id": ev.correlation_id,
        "timestamp": datetime_to_iso_utc(ev.timestamp) if ev.timestamp else None,
    }


def _serialize_event(ev: EventEnvelope) -> dict[str, Any]:
    """EventEnvelope to JSON-serializable dict (for pipeline_run.json). Timestamps via common util."""
    out = ev.model_dump(mode="json")
    out["timestamp"] = datetime_to_iso_utc(ev.timestamp) if ev.timestamp else None
    return out


def run_pipeline(
    raw_postings: list[dict],
    agent_slice: slice | None = None,
) -> dict[str, Any]:
    """
    Run the pipeline for each record. One correlation_id per record; same id through all stages.
    Returns the run log dict to be written to pipeline_run.json.
    """
    agents = PIPELINE_AGENTS[agent_slice] if agent_slice else PIPELINE_AGENTS
    run_id = str(uuid.uuid4())
    started_at = utc_now_iso()
    all_events: list[dict[str, Any]] = []

    for record_index, raw_record in enumerate(raw_postings):
        correlation_id = str(uuid.uuid4())
        # Initial event: runner injects this record; Ingestion uses payload["records"]
        event = EventEnvelope(
            correlation_id=correlation_id,
            agent_id="runner",
            payload={"records": [raw_record]},
        )
        log.info("record_entered", **_event_to_log_dict(event), record_index=record_index)

        for name, agent in agents:
            out = agent.process(event)
            if out is None:
                # Demand Analysis (Phase 2) returns None; log and append synthetic event so run log has one entry per agent per record
                synthetic = EventEnvelope(
                    correlation_id=correlation_id,
                    agent_id=agent.agent_id,
                    payload={"phase2_skipped": True, "message": "Phase 2 not implemented"},
                )
                log.info("event_emitted", **_event_to_log_dict(synthetic), phase2_skipped=True)
                all_events.append(_serialize_event(synthetic))
                continue
            if out.correlation_id != correlation_id:
                log.error(
                    "correlation_id_violation",
                    expected=correlation_id,
                    got=out.correlation_id,
                    agent_id=out.agent_id,
                )
                raise ValueError(f"Agent {out.agent_id} changed correlation_id")
            log.info("event_emitted", **_event_to_log_dict(out))
            all_events.append(_serialize_event(out))
            event = out

    finished_at = utc_now_iso()
    run_log = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "input_record_count": len(raw_postings),
        "events": all_events,
    }
    return run_log


def load_raw_postings(path: Path | None) -> list[dict]:
    """Load list of raw job postings from JSON file. If path is None, return minimal default."""
    if path is None or not path.exists():
        return [{"source": "runner", "title": "Default stub posting", "raw_text": ""}]
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "records" in data:
        return data["records"] if isinstance(data["records"], list) else []
    return []


def main() -> int:
    # Emit structlog to stdout (agent_id, event_id, correlation_id, timestamp per event)
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.KeyValueRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    parser = argparse.ArgumentParser(
        description="Run the Job Intelligence Engine pipeline over raw job postings."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="JSON file with list of raw postings (or object with 'records' key). Default: fallback_scrape_sample.json if present, else one stub.",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default=None,
        help="Optional slice of agents to run, e.g. 0:3 for first three (selectivity/debug).",
    )
    args = parser.parse_args()

    agent_slice = None
    if args.agents:
        try:
            parts = args.agents.split(":")
            if len(parts) == 1:
                agent_slice = slice(int(parts[0]), int(parts[0]) + 1)
            else:
                start = int(parts[0]) if parts[0] else 0
                stop = int(parts[1]) if parts[1] else len(PIPELINE_AGENTS)
                agent_slice = slice(start, stop)
        except ValueError:
            print("Invalid --agents; use e.g. 0:3 or 0:5", file=sys.stderr)
            return 1

    input_path = args.input if args.input is not None else (FALLBACK_SCRAPE_PATH if FALLBACK_SCRAPE_PATH.exists() else None)
    raw_postings = load_raw_postings(input_path)
    log.info("pipeline_start", record_count=len(raw_postings), agents_slice=str(agent_slice))

    _health_check_gate()

    run_log = run_pipeline(raw_postings, agent_slice=agent_slice)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PIPELINE_RUN_JSON.write_text(
        json.dumps(run_log, indent=2, default=str),
        encoding="utf-8",
    )
    log.info(
        "pipeline_complete",
        run_id=run_log["run_id"],
        output_path=str(PIPELINE_RUN_JSON),
        events_count=len(run_log["events"]),
    )
    print(f"Run log written to {PIPELINE_RUN_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
