"""Shared contracts and guardrails for message bus implementations.

Assumptions for Week 3 experiments:
- Events are batch-triggered and routed by payload ``event_type``.
- Every bus transports ``EventEnvelope`` objects as the shared contract.
- Orchestration-only control events are restricted to the
  ``orchestration-agent`` consumer.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeAlias, cast

from agents.common.event_envelope import EventEnvelope

EVENT_TYPE_KEY = "event_type"
MAX_EVENT_TYPE_LENGTH = 128
ORCHESTRATOR_AGENT_ID = "orchestration-agent"

_EVENT_TYPE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
_RESTRICTED_EVENT_SUFFIXES = ("Failed", "Alert")
ORCHESTRATION_ONLY_CONTROL_EVENTS = frozenset({
    "SourceFailure",
    "DemandAnomaly",
})


class MessageBusContractError(ValueError):
    """Base exception for invalid message bus contract usage."""


class InvalidEventTypeError(MessageBusContractError):
    """Raised when an event type is missing or invalid."""


class InvalidSubscriptionError(MessageBusContractError):
    """Raised when a subscription request is malformed."""


class RestrictedSubscriptionError(InvalidSubscriptionError):
    """Raised when a subscriber is not allowed to register for an event type."""


EventHandler: TypeAlias = Callable[[EventEnvelope], object | Awaitable[object] | None]


@dataclass(frozen=True, slots=True)
class Subscription:
    """Immutable subscription descriptor used across bus implementations."""

    event_type: str
    subscriber_id: str


def normalize_event_type(event_type: str) -> str:
    """Return a validated event type in canonical (trimmed) form."""
    if not isinstance(event_type, str):
        raise InvalidEventTypeError("event_type must be a string")

    normalized = event_type.strip()
    if not normalized:
        raise InvalidEventTypeError("event_type must be non-empty")

    if len(normalized) > MAX_EVENT_TYPE_LENGTH:
        raise InvalidEventTypeError(
            f"event_type exceeds max length ({MAX_EVENT_TYPE_LENGTH})"
        )

    if not _EVENT_TYPE_PATTERN.fullmatch(normalized):
        raise InvalidEventTypeError(
            "event_type must start with a letter and contain only letters, "
            "digits, '.', '_' or '-'"
        )

    return normalized


def extract_event_type(event: EventEnvelope) -> str:
    """Get and validate the routing event type from an envelope payload."""
    raw_event_type = event.payload.get(EVENT_TYPE_KEY)
    if raw_event_type is None:
        raise InvalidEventTypeError("event payload is missing required 'event_type'")

    if not isinstance(raw_event_type, str):
        raise InvalidEventTypeError("event payload field 'event_type' must be a string")

    return normalize_event_type(raw_event_type)


def validate_subscriber_id(subscriber_id: str) -> str:
    """Return a validated subscriber identifier."""
    if not isinstance(subscriber_id, str):
        raise InvalidSubscriptionError("subscriber_id must be a string")

    normalized = subscriber_id.strip()
    if not normalized:
        raise InvalidSubscriptionError("subscriber_id must be non-empty")

    return normalized


def validate_handler(handler: object) -> EventHandler:
    """Return a validated subscription handler."""
    if not callable(handler):
        raise InvalidSubscriptionError("handler must be callable")
    return cast(EventHandler, handler)


def is_restricted_control_event(event_type: str) -> bool:
    """True when only orchestration should subscribe to this event type."""
    normalized = normalize_event_type(event_type)
    return (
        normalized.endswith(_RESTRICTED_EVENT_SUFFIXES)
        or normalized in ORCHESTRATION_ONLY_CONTROL_EVENTS
    )


def enforce_subscription_policy(event_type: str, subscriber_id: str) -> Subscription:
    """Validate and normalize subscription inputs against architecture rules."""
    normalized_event_type = normalize_event_type(event_type)
    normalized_subscriber_id = validate_subscriber_id(subscriber_id)

    if (
        is_restricted_control_event(normalized_event_type)
        and normalized_subscriber_id != ORCHESTRATOR_AGENT_ID
    ):
        raise RestrictedSubscriptionError(
            f"only '{ORCHESTRATOR_AGENT_ID}' may subscribe to "
            f"'{normalized_event_type}' events"
        )

    return Subscription(
        event_type=normalized_event_type,
        subscriber_id=normalized_subscriber_id,
    )
