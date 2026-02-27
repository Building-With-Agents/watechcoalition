# agents.common.message_bus — In-process Python pub/sub (Phase 1). No external bus.

from agents.common.message_bus.bus import get_bus, MessageBus

__all__ = ["get_bus", "MessageBus"]
