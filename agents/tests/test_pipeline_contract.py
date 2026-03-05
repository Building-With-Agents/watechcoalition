from agents.common.base_agent import BaseAgent
from agents.common.events.base import SCHEMA_VERSION
from agents.common.pipeline.runner import health_check_all, run_pipeline
from agents.common.pipeline.stages import get_stages

EXPECTED_AGENT_IDS = [
    "ingestion",
    "normalization",
    "skills_extraction",
    "enrichment",
    "analytics",
    "visualization",
]


def test_run_pipeline_emits_six_events_with_one_correlation_id() -> None:
    events = run_pipeline(skip_health_check=True)

    assert len(events) == len(EXPECTED_AGENT_IDS)
    assert [event["agent_id"] for event in events] == EXPECTED_AGENT_IDS
    assert {event["schema_version"] for event in events} == {SCHEMA_VERSION}
    assert len({event["correlation_id"] for event in events}) == 1
    assert events[0]["payload"]["jobs"]
    assert events[-1]["payload"]["status"] == "complete"


def test_health_check_all_reports_all_pipeline_agents() -> None:
    health = health_check_all()

    assert set(health) == set(EXPECTED_AGENT_IDS)
    assert all(result["status"] == "ok" for result in health.values())
    assert all("last_run" in result for result in health.values())
    assert all(result.get("agent") in EXPECTED_AGENT_IDS for result in health.values())


def test_all_stages_extend_base_agent_and_expose_serializers() -> None:
    for stage_cls in get_stages():
        assert issubclass(stage_cls, BaseAgent)

        agent = stage_cls()

        state = agent.to_dict()
        audit = agent.to_audit_dict()

        assert state["agent_id"] == agent.AGENT_ID
        assert state["last_run"] is None
        assert state["metrics"] == {}
        assert audit["agent_id"] == agent.AGENT_ID
        assert audit["status"] == "ok"
        assert isinstance(audit["timestamp"], str)
