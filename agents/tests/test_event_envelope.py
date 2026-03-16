"""Tests for EventEnvelope — the typed event contract."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from agents.common.event_envelope import EventEnvelope


class TestEventEnvelope:
    """Verify the six required fields, defaults, validation, and serialization."""

    def test_event_id_auto_generated(self) -> None:
        """Each instantiation produces a valid UUID4 string."""
        env = EventEnvelope(
            correlation_id="c-1", agent_id="test-agent", payload={"k": "v"}
        )
        # Should be parseable as a UUID.
        parsed = uuid.UUID(env.event_id)
        assert parsed.version == 4

    def test_event_id_unique_across_instances(self) -> None:
        """Two envelopes created independently have different event_ids."""
        a = EventEnvelope(
            correlation_id="c-1", agent_id="test-agent", payload={}
        )
        b = EventEnvelope(
            correlation_id="c-1", agent_id="test-agent", payload={}
        )
        assert a.event_id != b.event_id

    def test_correlation_id_required(self) -> None:
        """Missing correlation_id raises a Pydantic ValidationError."""
        with pytest.raises(ValidationError):
            EventEnvelope(agent_id="test-agent", payload={})  # type: ignore[call-arg]

    def test_defaults(self) -> None:
        """Timestamp is auto-set and schema_version defaults to '1.0'."""
        env = EventEnvelope(
            correlation_id="c-1", agent_id="test-agent", payload={}
        )
        assert env.timestamp is not None
        assert env.schema_version == "1.0"

    def test_payload_accepts_arbitrary_dict(self) -> None:
        """Nested dicts, lists, and None values are all valid payload content."""
        payload = {
            "nested": {"a": [1, 2, 3]},
            "nullable": None,
            "flag": True,
        }
        env = EventEnvelope(
            correlation_id="c-1", agent_id="test-agent", payload=payload
        )
        assert env.payload["nested"]["a"] == [1, 2, 3]
        assert env.payload["nullable"] is None

    def test_json_round_trip(self) -> None:
        """model_dump() → EventEnvelope(**data) preserves all fields."""
        original = EventEnvelope(
            correlation_id="c-1",
            agent_id="test-agent",
            payload={"event_type": "TestEvent", "count": 42},
        )
        data = original.model_dump()
        restored = EventEnvelope(**data)

        assert restored.event_id == original.event_id
        assert restored.correlation_id == original.correlation_id
        assert restored.agent_id == original.agent_id
        assert restored.schema_version == original.schema_version
        assert restored.payload == original.payload
