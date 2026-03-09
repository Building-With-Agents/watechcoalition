"""Tests for Week 3 message bus shared contracts and policy helpers."""

from __future__ import annotations

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus.base import EventBusBase
from agents.common.message_bus.contracts import (
    ORCHESTRATOR_AGENT_ID,
    InvalidEventTypeError,
    InvalidSubscriptionError,
    RestrictedSubscriptionError,
    Subscription,
    enforce_subscription_policy,
    extract_event_type,
    is_restricted_control_event,
)


class _DummyBus(EventBusBase):
    """Minimal concrete class for validating base helper behavior."""

    def publish(self, event: EventEnvelope) -> None:
        return None

    def subscribe(self, event_type: str, handler, *, subscriber_id: str) -> Subscription:
        return self.validate_subscription(event_type, subscriber_id)


def test_extract_event_type_returns_normalized_value() -> None:
    event = EventEnvelope(
        correlation_id="c-1",
        agent_id="ingestion-agent",
        payload={"event_type": "  IngestBatch  "},
    )
    assert extract_event_type(event) == "IngestBatch"


def test_extract_event_type_rejects_missing_value() -> None:
    event = EventEnvelope(correlation_id="c-1", agent_id="ingestion-agent", payload={})
    with pytest.raises(InvalidEventTypeError):
        extract_event_type(event)


def test_extract_event_type_rejects_invalid_shape() -> None:
    event = EventEnvelope(
        correlation_id="c-1",
        agent_id="ingestion-agent",
        payload={"event_type": "bad type with spaces"},
    )
    with pytest.raises(InvalidEventTypeError):
        extract_event_type(event)


def test_restricted_control_event_detection() -> None:
    assert is_restricted_control_event("NormalizationFailed") is True
    assert is_restricted_control_event("SourceAlert") is True
    assert is_restricted_control_event("SourceFailure") is True
    assert is_restricted_control_event("DemandAnomaly") is True
    assert is_restricted_control_event("IngestBatch") is False


def test_subscription_policy_blocks_non_orchestrator_on_failed_events() -> None:
    with pytest.raises(RestrictedSubscriptionError):
        enforce_subscription_policy(
            event_type="NormalizationFailed",
            subscriber_id="normalization-agent",
        )


def test_subscription_policy_allows_orchestrator_on_failed_events() -> None:
    sub = enforce_subscription_policy(
        event_type="NormalizationFailed",
        subscriber_id=ORCHESTRATOR_AGENT_ID,
    )
    assert sub.event_type == "NormalizationFailed"
    assert sub.subscriber_id == ORCHESTRATOR_AGENT_ID


def test_subscription_policy_blocks_non_orchestrator_on_source_failure() -> None:
    with pytest.raises(RestrictedSubscriptionError):
        enforce_subscription_policy(
            event_type="SourceFailure",
            subscriber_id="ingestion-agent",
        )


def test_subscription_policy_blocks_non_orchestrator_on_demand_anomaly() -> None:
    with pytest.raises(RestrictedSubscriptionError):
        enforce_subscription_policy(
            event_type="DemandAnomaly",
            subscriber_id="analytics-agent",
        )


def test_event_bus_base_helper_methods_delegate_to_contracts() -> None:
    bus = _DummyBus()
    event = EventEnvelope(
        correlation_id="c-1",
        agent_id="ingestion-agent",
        payload={"event_type": "IngestBatch"},
    )

    assert bus.event_type_for(event) == "IngestBatch"
    sub = bus.subscribe(
        event_type="IngestBatch",
        handler=lambda evt: evt,
        subscriber_id="normalization-agent",
    )
    assert sub == Subscription(event_type="IngestBatch", subscriber_id="normalization-agent")


def test_event_bus_base_rejects_non_callable_subscription_handler() -> None:
    bus = _DummyBus()
    with pytest.raises(InvalidSubscriptionError):
        bus.validate_subscription_handler(handler="not-callable")
