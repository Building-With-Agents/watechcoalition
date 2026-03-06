"""Tests for BaseAgent — the abstract interface every agent implements."""

from __future__ import annotations

import pytest

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class TestBaseAgent:
    """Verify the abstract interface and agent_id storage."""

    def test_health_check_raises_not_implemented(self) -> None:
        """Calling health_check() on BaseAgent directly raises NotImplementedError."""
        agent = BaseAgent(agent_id="raw-base")
        with pytest.raises(NotImplementedError):
            agent.health_check()

    def test_process_raises_not_implemented(self) -> None:
        """Calling process() on BaseAgent directly raises NotImplementedError."""
        agent = BaseAgent(agent_id="raw-base")
        event = EventEnvelope(
            correlation_id="c-1", agent_id="test", payload={}
        )
        with pytest.raises(NotImplementedError):
            agent.process(event)

    def test_agent_id_stored(self) -> None:
        """The agent_id passed to __init__ is stored and retrievable."""
        agent = BaseAgent(agent_id="my-custom-agent")
        assert agent.agent_id == "my-custom-agent"
