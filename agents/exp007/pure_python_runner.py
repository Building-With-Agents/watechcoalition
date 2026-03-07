"""
EXP-007: Two-agent pipeline (Ingestion → Normalization) in pure Python.

State machine: initial event → IngestionAgent.process() → NormalizationAgent.process() → end.
Same state shape and contract as the LangGraph runner for direct comparison.
No framework dependency.

Run from repo root:
    python agents/exp007/pure_python_runner.py

Or: run_two_agent_pure_python(raw_posting_dict)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import structlog

# Path bootstrap: repo root on sys.path for "from agents.*" imports.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents.common.event_envelope import EventEnvelope  # noqa: E402
from agents.exp007.state import TwoAgentPipelineState  # noqa: E402
from agents.ingestion.agent import IngestionAgent  # noqa: E402
from agents.normalization.agent import NormalizationAgent  # noqa: E402

_INGESTION_AGENT = IngestionAgent()
_NORMALIZATION_AGENT = NormalizationAgent()

log = structlog.get_logger()


def run_two_agent_pure_python(
    raw_posting: dict,
    correlation_id: str | None = None,
) -> TwoAgentPipelineState:
    """
    Run one raw posting through the two-agent pipeline (Ingestion → Normalization).

    Pure Python state machine: no LangGraph. Same inputs/outputs as run_two_agent_langgraph.
    """
    cid = correlation_id or str(raw_posting.get("posting_id", "run-1"))
    event = EventEnvelope(
        correlation_id=cid,
        agent_id="pipeline-runner",
        payload=raw_posting,
    )

    # Pipeline topology (2-agent): ingestion → normalization
    event = _INGESTION_AGENT.process(event)
    event = _NORMALIZATION_AGENT.process(event)

    return {
        "current_event": event.model_dump(mode="json"),
        "correlation_id": event.correlation_id,
        "status": "ok",
    }


def run_from_after_ingestion_pure_python(event: EventEnvelope) -> TwoAgentPipelineState:
    """
    Resume from the last successful step: run only Normalization (no Ingestion).

    Use after a crash in Normalization: pass the IngestBatch event produced by
    IngestionAgent; this runs NormalizationAgent only. Ingestion is not invoked.
    """
    event = _NORMALIZATION_AGENT.process(event)
    return {
        "current_event": event.model_dump(mode="json"),
        "correlation_id": event.correlation_id,
        "status": "ok",
    }


def main() -> None:
    """Load one posting from fallback scrape and run through pure Python two-agent pipeline."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "data" / "fixtures"
    fallback = fixtures_dir / "fallback_scrape_sample.json"
    if not fallback.exists():
        log.error("fixture_not_found", path=str(fallback))
        sys.exit(1)

    postings = json.loads(fallback.read_text(encoding="utf-8"))
    posting = postings[0]
    correlation_id = str(posting.get("posting_id", "1"))

    state = run_two_agent_pure_python(posting, correlation_id=correlation_id)
    event_type = state.get("current_event", {}).get("payload", {}).get("event_type")
    log.info(
        "pure_python_run_complete",
        event_type=event_type,
        correlation_id=state.get("correlation_id"),
        status=state.get("status"),
    )


if __name__ == "__main__":
    main()
