"""
Sequential pipeline runner for the Walking Skeleton.
Runs 10 fixture records through all 8 agents in order; logs and writes run_log to JSON.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog

from agents.analytics.agent import AnalyticsAgent
from agents.common.event_envelope import EventEnvelope
from agents.demand_analysis.agent import DemandAnalysisAgent
from agents.enrichment.agent import EnrichmentAgent
from agents.ingestion.agent import IngestionAgent
from agents.normalization.agent import NormalizationAgent
from agents.orchestration.agent import OrchestrationAgent
from agents.skills_extraction.agent import SkillsExtractionAgent
from agents.visualization.agent import VisualizationAgent

# Ordered agent list per architectural spine
AGENTS = [
    IngestionAgent(),
    NormalizationAgent(),
    SkillsExtractionAgent(),
    EnrichmentAgent(),
    DemandAnalysisAgent(),
    AnalyticsAgent(),
    VisualizationAgent(),
    OrchestrationAgent(),
]

# Single source of input data for the loop; no other file is loaded for pipeline input.
_AGENTS_DIR = Path(__file__).resolve().parent
SOURCE_FIXTURE_PATH = _AGENTS_DIR / "data" / "fixtures" / "fallback_scrape_sample.json"
OUTPUT_PATH = _AGENTS_DIR / "data" / "output" / "pipeline_run.json"
NUM_RECORDS = 10

log = structlog.get_logger()


def _event_to_log_dict(event: EventEnvelope) -> dict:
    """Serialize event to JSON-serializable dict for run_log."""
    return event.model_dump(mode="json")


def main() -> None:
    # 1. Health check gate
    for agent in AGENTS:
        health = agent.health_check()
        if health.get("status") != "healthy":
            log.warning("agent_health_failed", agent_id=agent.agent_id, health=health)
            raise RuntimeError(f"Agent {agent.agent_id} failed health check: {health}")

    # 2. Load 10 source records from fallback_scrape_sample.json only
    with open(SOURCE_FIXTURE_PATH, encoding="utf-8") as f:
        all_records = json.load(f)
    records = all_records[:NUM_RECORDS]

    run_log: list[dict] = []

    # 3. Outer loop: one record at a time
    for record in records:
        correlation_id = str(uuid.uuid4())
        current_envelope = EventEnvelope(
            correlation_id=correlation_id,
            agent_id="pipeline_runner",
            payload=record if isinstance(record, dict) else {"record": record},
        )

        # 4. Inner loop: pass through 8 agents in sequence
        for agent in AGENTS:
            result = agent.process(current_envelope)

            if result is None:
                # Phase 2 skip (DemandAnalysisAgent)
                log.info(
                    "Phase2Skipped",
                    agent_id=agent.agent_id,
                    correlation_id=correlation_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                run_log.append({
                    "phase2_skipped": True,
                    "agent_id": agent.agent_id,
                    "correlation_id": correlation_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                # Keep current_envelope for next agent
                continue

            # Successful execution
            log.info(
                "agent_execution",
                agent_id=result.agent_id,
                event_id=result.event_id,
                correlation_id=result.correlation_id,
                timestamp=result.timestamp.isoformat() if hasattr(result.timestamp, "isoformat") else str(result.timestamp),
            )
            run_log.append(_event_to_log_dict(result))
            current_envelope = result

    # 5. Write run_log to output file
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(run_log, f, indent=2)

    log.info("pipeline_run_complete", output_path=str(OUTPUT_PATH), run_log_entries=len(run_log))


if __name__ == "__main__":
    main()
