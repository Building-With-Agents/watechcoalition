"""Tests for AgentBase — the abstract interface every agent implements."""

from __future__ import annotations

import pytest

from agents.common.base_agent import AgentBase, BaseAgent
from agents.common.event_envelope import EventEnvelope


class _ConcreteAgent(AgentBase):
    """Minimal concrete subclass for testing the ABC contract."""

    @property
    def agent_id(self) -> str:
        return "test-agent"

    def health_check(self) -> dict:
        return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=event.payload,
        )


class TestAgentBase:
    """Verify the abstract interface and property-based agent_id."""

    def test_cannot_instantiate_directly(self) -> None:
        """AgentBase is abstract — direct instantiation raises TypeError."""
        with pytest.raises(TypeError):
            AgentBase()  # type: ignore[abstract]

    def test_backward_compat_alias(self) -> None:
        """BaseAgent is an alias for AgentBase."""
        assert BaseAgent is AgentBase

    def test_concrete_subclass_agent_id(self) -> None:
        """A concrete subclass exposes agent_id as a property."""
        agent = _ConcreteAgent()
        assert agent.agent_id == "test-agent"

    def test_concrete_subclass_health_check(self) -> None:
        """A concrete subclass returns a valid health check dict."""
        agent = _ConcreteAgent()
        result = agent.health_check()
        assert result["status"] == "ok"
        assert result["agent"] == "test-agent"

    def test_concrete_subclass_process(self) -> None:
        """A concrete subclass processes an event and preserves correlation_id."""
        agent = _ConcreteAgent()
        event = EventEnvelope(correlation_id="c-1", agent_id="upstream", payload={"key": "value"})
        out = agent.process(event)
        assert out.correlation_id == "c-1"
        assert out.agent_id == "test-agent"
        assert out.payload == {"key": "value"}

    def test_missing_agent_id_raises(self) -> None:
        """A subclass missing agent_id cannot be instantiated."""

        class _NoAgentId(AgentBase):
            def health_check(self) -> dict:
                return {}

            def process(self, event: EventEnvelope) -> EventEnvelope | None:
                return None

        with pytest.raises(TypeError):
            _NoAgentId()  # type: ignore[call-arg]

    def test_missing_health_check_raises(self) -> None:
        """A subclass missing health_check cannot be instantiated."""

        class _NoHealthCheck(AgentBase):
            @property
            def agent_id(self) -> str:
                return "incomplete"

            def process(self, event: EventEnvelope) -> EventEnvelope | None:
                return None

        with pytest.raises(TypeError):
            _NoHealthCheck()  # type: ignore[abstract]

    def test_missing_process_raises(self) -> None:
        """A subclass missing process cannot be instantiated."""

        class _NoProcess(AgentBase):
            @property
            def agent_id(self) -> str:
                return "incomplete"

            def health_check(self) -> dict:
                return {}

        with pytest.raises(TypeError):
            _NoProcess()  # type: ignore[abstract]
