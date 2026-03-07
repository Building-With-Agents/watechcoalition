"""EXP-007 Day 1c: Crash test — resume from after Ingestion without re-running it."""

from __future__ import annotations

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.exp007.langgraph_runner import run_from_after_ingestion_langgraph
from agents.exp007.pure_python_runner import run_from_after_ingestion_pure_python
from agents.ingestion.agent import IngestionAgent


def _ingestion_output_event() -> EventEnvelope:
    """Produce IngestBatch event (last successful step before Normalization)."""
    agent = IngestionAgent()
    initial = EventEnvelope(
        correlation_id="test-resume-1",
        agent_id="pipeline-runner",
        payload={
            "posting_id": 1,
            "source": "web_scrape",
            "title": "Senior Data Engineer",
            "company": "Microsoft",
            "location": "Redmond, WA",
        },
    )
    return agent.process(initial)


def test_resume_from_after_ingestion_langgraph_returns_normalization_complete() -> None:
    """Resume (normalization only) via LangGraph returns NormalizationComplete."""
    ingestion_output = _ingestion_output_event()
    assert ingestion_output.payload.get("event_type") == "IngestBatch"

    state = run_from_after_ingestion_langgraph(ingestion_output)
    event_type = state.get("current_event", {}).get("payload", {}).get("event_type")
    assert event_type == "NormalizationComplete"
    assert state.get("correlation_id") == "test-resume-1"


def test_resume_from_after_ingestion_pure_python_returns_normalization_complete() -> None:
    """Resume (normalization only) via pure Python returns NormalizationComplete."""
    ingestion_output = _ingestion_output_event()
    assert ingestion_output.payload.get("event_type") == "IngestBatch"

    state = run_from_after_ingestion_pure_python(ingestion_output)
    event_type = state.get("current_event", {}).get("payload", {}).get("event_type")
    assert event_type == "NormalizationComplete"
    assert state.get("correlation_id") == "test-resume-1"
