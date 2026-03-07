"""
EXP-007: Two-agent pipeline (Ingestion → Normalization) in LangGraph.

Uses existing IngestionState/NormalizationState concepts via a single
TwoAgentPipelineState that carries the current EventEnvelope (as dict)
through the graph. Each node calls AgentBase.process() on the stub agents.

Run from repo root:
    python agents/exp007/langgraph_runner.py

Or import and call run_two_agent_langgraph(raw_posting_dict).
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

# LangGraph: StateGraph, START, END
try:
    from langgraph.graph import END, START, StateGraph  # noqa: E402
except ImportError as e:
    raise ImportError(
        "LangGraph is required for EXP-007 LangGraph runner. "
        "Install with: pip install langgraph>=0.2"
    ) from e

# Agent instances (stub implementations; same as pipeline_runner.py)
_INGESTION_AGENT = IngestionAgent()
_NORMALIZATION_AGENT = NormalizationAgent()

log = structlog.get_logger()


def _event_from_state(state: TwoAgentPipelineState) -> EventEnvelope:
    """Build EventEnvelope from state['current_event'] dict."""
    raw = state.get("current_event")
    if not raw:
        raise ValueError("state['current_event'] is required")
    return EventEnvelope.model_validate(raw)


def _ingestion_node(state: TwoAgentPipelineState) -> dict:
    """LangGraph node: run IngestionAgent.process() and update state."""
    envelope = _event_from_state(state)
    out = _INGESTION_AGENT.process(envelope)
    return {
        "current_event": out.model_dump(mode="json"),
        "correlation_id": out.correlation_id,
        "status": "ok",
    }


def _normalization_node(state: TwoAgentPipelineState) -> dict:
    """LangGraph node: run NormalizationAgent.process() and update state."""
    envelope = _event_from_state(state)
    out = _NORMALIZATION_AGENT.process(envelope)
    return {
        "current_event": out.model_dump(mode="json"),
        "correlation_id": out.correlation_id,
        "status": "ok",
    }


def build_two_agent_graph() -> StateGraph:
    """
    Build the Ingestion → Normalization StateGraph.

    Topology: START → ingestion → normalization → END.
    State: TwoAgentPipelineState (current_event, correlation_id, status, errors).
    """
    graph = StateGraph(TwoAgentPipelineState)

    graph.add_node("ingestion", _ingestion_node)
    graph.add_node("normalization", _normalization_node)

    graph.add_edge(START, "ingestion")
    graph.add_edge("ingestion", "normalization")
    graph.add_edge("normalization", END)

    return graph.compile()


def run_two_agent_langgraph(
    raw_posting: dict,
    correlation_id: str | None = None,
) -> TwoAgentPipelineState:
    """
    Run one raw posting through the two-agent LangGraph pipeline.

    Args:
        raw_posting: Raw job posting dict (e.g. from fallback_scrape_sample.json).
        correlation_id: Optional; defaults to posting_id or a generated id.

    Returns:
        Final state dict with current_event (NormalizationComplete), status, etc.
    """
    cid = correlation_id or str(raw_posting.get("posting_id", "run-1"))
    initial = EventEnvelope(
        correlation_id=cid,
        agent_id="pipeline-runner",
        payload=raw_posting,
    )
    initial_state: TwoAgentPipelineState = {
        "current_event": initial.model_dump(mode="json"),
        "correlation_id": cid,
        "status": "ok",
    }

    app = build_two_agent_graph()
    # invoke returns the final state (after END)
    result = app.invoke(initial_state)
    return result


def main() -> None:
    """Load one posting from fallback scrape and run through LangGraph pipeline."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "data" / "fixtures"
    fallback = fixtures_dir / "fallback_scrape_sample.json"
    if not fallback.exists():
        log.error("fixture_not_found", path=str(fallback))
        sys.exit(1)

    postings = json.loads(fallback.read_text(encoding="utf-8"))
    posting = postings[0]
    correlation_id = str(posting.get("posting_id", "1"))

    state = run_two_agent_langgraph(posting, correlation_id=correlation_id)
    event_type = state.get("current_event", {}).get("payload", {}).get("event_type")
    log.info(
        "langgraph_run_complete",
        event_type=event_type,
        correlation_id=state.get("correlation_id"),
        status=state.get("status"),
    )


if __name__ == "__main__":
    main()
