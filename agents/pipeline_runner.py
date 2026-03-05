"""
Pipeline runner — chains all eight agents, health-check gate, correlation_id propagation, structlog, run log.

Run from repo root:
  python -m agents.pipeline_runner
  PIPELINE_AGENT_LIMIT=7 python -m agents.pipeline_runner   # skip Demand Analysis (Phase 2 stub returns degraded)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import structlog

from agents.common.event_envelope import EventEnvelope
from agents.ingestion.agent import IngestionAgent
from agents.normalization.agent import NormalizationAgent
from agents.skills_extraction.agent import SkillsExtractionAgent
from agents.enrichment.agent import EnrichmentAgent
from agents.analytics.agent import AnalyticsAgent
from agents.visualization.agent import VisualizationAgent
from agents.orchestration.agent import OrchestrationAgent
from agents.demand_analysis.agent import DemandAnalysisAgent

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.get_logger()

# Ordered list of (agent_factory, use_output_as_next_input).
# Demand Analysis returns None so we do not use its output as next input.
AGENT_CHAIN = [
    (IngestionAgent, True),
    (NormalizationAgent, True),
    (SkillsExtractionAgent, True),
    (EnrichmentAgent, True),
    (AnalyticsAgent, True),
    (VisualizationAgent, True),
    (OrchestrationAgent, True),
    (DemandAnalysisAgent, False),  # Phase 2 stub: process() returns None
]


def _agents_root() -> Path:
    return Path(__file__).resolve().parent


def _output_dir() -> Path:
    return _agents_root() / "data" / "output"


def _get_agent_limit() -> int:
    try:
        return int(os.getenv("PIPELINE_AGENT_LIMIT", str(len(AGENT_CHAIN))))
    except ValueError:
        return len(AGENT_CHAIN)


def _health_ok(health: dict, agent_id: str) -> bool:
    """True if agent is healthy. Phase 2 stubs (e.g. demand_analysis_agent) may return 'degraded'; allow that."""
    status = health.get("status")
    if status == "ok":
        return True
    if status == "degraded" and agent_id == "demand_analysis_agent":
        return True
    return False


def run_health_checks(agent_limit: int) -> list:
    """Instantiate agents up to agent_limit, run health_check() on each. Return list of (agent_instance, health_result)."""
    agents_and_health = []
    for i, (agent_cls, _) in enumerate(AGENT_CHAIN):
        if i >= agent_limit:
            break
        agent = agent_cls()
        health = agent.health_check()
        agents_and_health.append((agent, health))
        if not _health_ok(health, health.get("agent", "")):
            log.error(
                "health_check_failed",
                agent_id=health.get("agent"),
                status=health.get("status"),
                metrics=health.get("metrics"),
            )
            return agents_and_health
    return agents_and_health


def run_pipeline(
    raw_postings: list[dict],
    agent_limit: int | None = None,
) -> dict:
    """
    Run health checks, then pass one initial event per run through the agent chain.
    One correlation_id per run; each record is represented in the initial payload.
    """
    if agent_limit is None:
        agent_limit = _get_agent_limit()
    agents_and_health = run_health_checks(agent_limit)
    for agent, health in agents_and_health:
        if not _health_ok(health, health.get("agent", "")):
            msg = f"Pipeline aborted: agent {health.get('agent')} status is {health.get('status')}."
            print(msg, file=sys.stderr)
            log.error("pipeline_abort", reason=msg, agent_id=health.get("agent"), status=health.get("status"))
            return {"aborted": True, "reason": msg, "run_log": []}

    correlation_id = str(uuid4())
    # Initial event: trigger with payload that the first agent (Ingestion) can use or ignore (stub loads fixture).
    event = EventEnvelope(
        correlation_id=correlation_id,
        agent_id="pipeline_runner",
        payload={"records": raw_postings, "batch_id": correlation_id},
    )
    run_log: list[dict] = []

    for i, (agent, _) in enumerate(agents_and_health):
        if i == 0:
            current_event = event
        # Process through this agent
        out = agent.process(current_event)
        if out is not None:
            log.info(
                "event_emitted",
                agent_id=out.agent_id,
                event_id=out.event_id,
                correlation_id=out.correlation_id,
                timestamp=out.timestamp.isoformat() if hasattr(out.timestamp, "isoformat") else str(out.timestamp),
            )
            run_log.append({
                "agent_id": out.agent_id,
                "event_id": out.event_id,
                "correlation_id": out.correlation_id,
                "timestamp": out.timestamp.isoformat() if hasattr(out.timestamp, "isoformat") else str(out.timestamp),
                "payload_keys": list(out.payload.keys()) if out.payload else [],
            })
            current_event = out
        else:
            # Demand Analysis (or any agent that returns None)
            log.info("agent_returned_none", agent_id=agent.agent_id, correlation_id=correlation_id)
            run_log.append({
                "agent_id": agent.agent_id,
                "event_id": None,
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload_keys": [],
                "note": "process() returned None",
            })

    return {
        "aborted": False,
        "correlation_id": correlation_id,
        "agents_run": len(agents_and_health),
        "run_log": run_log,
    }


def main() -> None:
    # Stub input: empty or a couple of raw postings for a single batch
    raw_postings: list[dict] = [
        {"title": "Software Engineer", "company": "Acme Corp", "location": "Seattle"},
        {"title": "Data Analyst", "company": "Beta Inc", "location": "Remote"},
    ]
    agent_limit = _get_agent_limit()
    result = run_pipeline(raw_postings, agent_limit=agent_limit)
    out_dir = _output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pipeline_run.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    log.info("run_log_written", path=str(out_path), aborted=result.get("aborted", False))
    if result.get("aborted"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
