"""Re-export EventEnvelope from its canonical location.

This module exists so that ``from agents.common.events import EventEnvelope``
works alongside the original ``from agents.common.event_envelope import EventEnvelope``.
"""

from agents.common.event_envelope import EventEnvelope  # noqa: F401

__all__ = ["EventEnvelope"]
