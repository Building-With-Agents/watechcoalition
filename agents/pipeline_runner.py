# agents/pipeline_runner.py
"""
Pipeline runner: accepts raw job postings, runs health checks on all agents,
then passes each record through the eight agents in sequence.
Each record keeps the same correlation_id across all stages.
Logs every event with structlog and writes the full run log to pipeline_run.json.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

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


log = structlog.get_logger()

# Output path for the run log (agents/data/output/pipeline_run.json)
RUN_LOG_PATH = Path(__file__).resolve().parent / "data" / "output" / "pipeline_run.json"

# All eight agents in pipeline order
PIPELINE_AGENTS = [
    ("ingestion_agent", IngestionAgent),
    ("normalization_agent", NormalizationAgent),
    ("skills_extraction_agent", SkillsExtractionAgent),
    ("enrichment_agent", EnrichmentAgent),
    ("analytics_agent", AnalyticsAgent),
    ("visualization_agent", VisualizationAgent),
    ("orchestration_agent", OrchestrationAgent),
    ("demand_analysis_agent", DemandAnalysisAgent),
]


def _agent_instances():
    """Return a list of (agent_id, instance) for all eight agents."""
    return [(aid, cls()) for aid, cls in PIPELINE_AGENTS]


def run_health_checks() -> tuple[bool, list[dict]]:
    """
    Run health_check() on all eight agents.
    Returns (all_ok, list of health check results).
    """
    results = []
    all_ok = True
    for agent_id, agent in _agent_instances():
        try:
            h = agent.health_check()
            results.append(h)
            status = h.get("status", "down")
            if status not in ("ok", "degraded"):
                all_ok = False
            log.info(
                "health_check",
                agent_id=agent_id,
                status=status,
                metrics=h.get("metrics"),
            )
        except Exception as e:
            all_ok = False
            results.append({"agent": agent_id, "status": "down", "error": str(e)})
            log.exception("health_check_failed", agent_id=agent_id, error=str(e))
    return all_ok, results


def _envelope_to_log_dict(envelope: EventEnvelope) -> dict:
    """Serialize EventEnvelope to a JSON-serializable dict (timestamps as ISO strings)."""
    return envelope.model_dump(mode="json")


def run_pipeline(raw_postings: list[dict]) -> dict:
    """
    Run the full pipeline on a list of raw job postings.

    1. Run health checks on all eight agents; abort if any is unhealthy.
    2. For each record, assign a correlation_id and pass through all eight agents.
    3. Log every event with structlog (agent_id, event_id, correlation_id, timestamp).
    4. Write the full run log to agents/data/output/pipeline_run.json.

    Returns a summary dict with keys: success, health_checks_passed, records_processed,
    total_events, run_log_path, errors (list of per-record errors if any).
    """
    # Health checks first
    health_ok, health_results = run_health_checks()
    if not health_ok:
        log.error("pipeline_aborted", reason="unhealthy_agent", health_results=health_results)
        return {
            "success": False,
            "health_checks_passed": False,
            "records_processed": 0,
            "total_events": 0,
            "run_log_path": None,
            "errors": ["One or more agents failed health check; pipeline aborted."],
        }

    log.info("health_checks_passed", all_agents_ok=True)
    run_log: list[dict] = []
    errors: list[str] = []
    agents = _agent_instances()  # list of (agent_id, instance)

    for raw in raw_postings:
        correlation_id = str(uuid.uuid4())
        # Initial envelope: payload = raw posting; correlation_id set for the whole chain
        envelope = EventEnvelope(
            correlation_id=correlation_id,
            agent_id="pipeline_runner",
            payload=raw,
        )

        for agent_id, agent in agents:
            try:
                out = agent.process(envelope)
                if out is not None:
                    log.info(
                        "event_emitted",
                        agent_id=out.agent_id,
                        event_id=out.event_id,
                        correlation_id=out.correlation_id,
                        timestamp=out.timestamp.isoformat(),
                    )
                    run_log.append(_envelope_to_log_dict(out))
                    envelope = out
                else:
                    log.info(
                        "agent_returned_none",
                        agent_id=agent_id,
                        correlation_id=correlation_id,
                    )
                    run_log.append({
                        "correlation_id": correlation_id,
                        "stage": agent_id,
                        "event": None,
                        "reason": "agent_returned_none",
                    })
            except Exception as e:
                log.exception(
                    "agent_error",
                    agent_id=agent_id,
                    correlation_id=correlation_id,
                    error=str(e),
                )
                errors.append(f"{agent_id} correlation_id={correlation_id}: {e}")
                run_log.append({
                    "correlation_id": correlation_id,
                    "stage": agent_id,
                    "event": None,
                    "error": str(e),
                })
                break  # stop this record's chain

    # Write run log to agents/data/output/pipeline_run.json
    RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RUN_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_at": datetime.utcnow().isoformat() + "Z",
                "records_processed": len(raw_postings),
                "total_events": len(run_log),
                "events": run_log,
            },
            f,
            indent=2,
        )

    log.info(
        "pipeline_run_complete",
        records_processed=len(raw_postings),
        total_events=len(run_log),
        run_log_path=str(RUN_LOG_PATH),
    )

    return {
        "success": len(errors) == 0,
        "health_checks_passed": True,
        "records_processed": len(raw_postings),
        "total_events": len(run_log),
        "run_log_path": str(RUN_LOG_PATH),
        "errors": errors,
    }


if __name__ == "__main__":
    # Example: run with a minimal raw posting from fixtures
    import sys
    fixtures_dir = Path(__file__).resolve().parent / "data" / "fixtures"
    sample = fixtures_dir / "fallback_scrape_sample.json"
    if sample.exists():
        with open(sample, encoding="utf-8") as f:
            data = json.load(f)
        postings = data if isinstance(data, list) else [data]
    else:
        postings = [
            {
                "posting_id": "sample-1",
                "source": "web_scrape",
                "url": "https://example.com/job/1",
                "title": "Software Engineer",
                "company": "Acme Inc",
                "location": "Remote",
                "timestamp": datetime.utcnow().isoformat(),
                "raw_text": "Sample description",
            }
        ]

    if len(sys.argv) > 1 and sys.argv[1] == "--count":
        try:
            n = int(sys.argv[2])
            postings = postings * n
        except (IndexError, ValueError):
            pass

    result = run_pipeline(postings)
    print(json.dumps(result, indent=2))
