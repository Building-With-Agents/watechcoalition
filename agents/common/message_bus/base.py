"""Transport-agnostic event bus abstraction for Week 3 experiments."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus.contracts import (
    EventHandler,
    Subscription,
    enforce_subscription_policy,
    extract_event_type,
    validate_handler,
)


class EventBusBase(ABC):
    """Base contract shared by in-process, Redis Streams, and Kafka buses."""

    @staticmethod
    def event_type_for(event: EventEnvelope) -> str:
        """Extract and validate the routing event type from an event envelope."""
        return extract_event_type(event)

    @staticmethod
    def validate_subscription(event_type: str, subscriber_id: str) -> Subscription:
        """Validate subscription inputs and enforce control-event restrictions."""
        return enforce_subscription_policy(event_type, subscriber_id)

    @staticmethod
    def validate_subscription_handler(handler: object) -> EventHandler:
        """Validate subscription handler shape."""
        return validate_handler(handler)

    @abstractmethod
    def publish(self, event: EventEnvelope) -> None:
        """Publish an event without assuming immediate synchronous delivery."""

    @abstractmethod
    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        *,
        subscriber_id: str,
    ) -> Subscription:
        """Register a sync or async handler for one event type."""
