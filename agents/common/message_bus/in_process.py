"""In-process event bus baseline for Week 3 transport experiments."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable
from inspect import isawaitable
from typing import cast

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus.base import EventBusBase
from agents.common.message_bus.contracts import EventHandler, Subscription


class InProcessEventBus(EventBusBase):
    """Synchronous in-memory pub/sub bus with minimal instrumentation counters."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[tuple[Subscription, EventHandler]]] = (
            defaultdict(list)
        )
        self._published_events = 0
        self._delivered_events = 0
        self._handler_failures = 0

    @property
    def counters(self) -> dict[str, int]:
        """Snapshot instrumentation counters for experiment comparisons."""
        return {
            "published_events": self._published_events,
            "delivered_events": self._delivered_events,
            "handler_failures": self._handler_failures,
        }

    def publish(self, event: EventEnvelope) -> None:
        """Publish one event to all subscribers of its routing event type."""
        event_type = self.event_type_for(event)
        self._published_events += 1

        for _, handler in tuple(self._subscribers.get(event_type, ())):
            try:
                result = handler(event)
                if isawaitable(result):
                    asyncio.run(cast(Awaitable[object], result))
                self._delivered_events += 1
            except Exception:
                self._handler_failures += 1

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        *,
        subscriber_id: str,
    ) -> Subscription:
        """Register a handler under one validated event type."""
        subscription = self.validate_subscription(event_type, subscriber_id)
        validated_handler = self.validate_subscription_handler(handler)
        self._subscribers[subscription.event_type].append(
            (subscription, validated_handler)
        )
        return subscription
