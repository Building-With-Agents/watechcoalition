from __future__ import annotations

from agents.common.base_agent import BaseAgent
from agents.common.events.base import SCHEMA_VERSION, create_event
from agents.demand_analysis.agent import DemandAnalysisAgent
from agents.orchestration.agent import OrchestrationAgent


def test_week2_stub_agents_extend_base_agent_and_expose_serializers() -> None:
    for agent_cls in (DemandAnalysisAgent, OrchestrationAgent):
        assert issubclass(agent_cls, BaseAgent)

        agent = agent_cls()
        state = agent.to_dict()
        audit = agent.to_audit_dict()

        assert state["agent_id"] == agent.AGENT_ID
        assert state["last_run"] is None
        assert isinstance(state["metrics"], dict)
        assert audit["agent_id"] == agent.AGENT_ID
        assert audit["status"] == "ok"
        assert isinstance(audit["timestamp"], str)


def test_demand_analysis_stub_emits_event() -> None:
    upstream = create_event(
        correlation_id="run-test-123",
        agent_id="analytics",
        schema_version=SCHEMA_VERSION,
        payload={"total_postings": 10},
    )
    agent = DemandAnalysisAgent()

    event = agent.process(upstream)

    assert event is not None
    assert event.agent_id == "demand_analysis"
    assert event.correlation_id == upstream.correlation_id
    assert event.payload["status"] == "stub_only"
    assert event.payload["record_count"] == 10


def test_orchestration_stub_emits_observation_event() -> None:
    upstream = create_event(
        correlation_id="run-test-456",
        agent_id="visualization",
        schema_version=SCHEMA_VERSION,
        payload={"status": "complete"},
    )
    agent = OrchestrationAgent()

    event = agent.process(upstream)

    assert event is not None
    assert event.agent_id == "orchestration"
    assert event.correlation_id == upstream.correlation_id
    assert event.payload["observed_agent_id"] == "visualization"
    assert event.payload["mode"] == "sequential_stub"
