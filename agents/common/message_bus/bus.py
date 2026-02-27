# agents/common/message_bus/bus.py
"""In-process pub/sub for Phase 1. Events-only; no external message bus."""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Callable

from agents.common.events import AgentEvent


class MessageBus:
    """In-process subscribe/publish. One bus per process."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # event_type -> list of callbacks
        self._subscribers: dict[str, list[Callable[[AgentEvent], None]]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[AgentEvent], None]) -> None:
        with self._lock:
            self._subscribers[event_type].append(handler)

    def publish(self, event: AgentEvent, event_type: str) -> None:
        with self._lock:
            handlers = list(self._subscribers[event_type])
        for h in handlers:
            try:
                h(event)
            except Exception:
                # Log but do not break other subscribers
                pass

    def clear(self) -> None:
        """For tests only."""
        with self._lock:
            self._subscribers.clear()


_bus: MessageBus | None = None


def get_bus() -> MessageBus:
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus
