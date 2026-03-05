"""
EventEnvelope — a reserved typed event model kept for future experiments.

Deprecated for the active pipeline implementation.

The walking skeleton and current pipeline standardize on `AgentEvent`
from `agents.common.events.base`. Keep this model only as a reserved
typed wrapper for future experiments or migrations; do not use it for
inter-agent communication in the current pipeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """
    Typed, versioned event contract for the Job Intelligence Engine pipeline.

    Fields
    ------
    event_id       : Unique identifier for this specific event (UUID4).
                     Generated automatically; never reused.

    correlation_id : Ties all events produced by a single pipeline run for
                     one job record together.  Set once by the pipeline runner
                     when the record enters the pipeline; carried through every
                     subsequent agent unchanged.

    agent_id       : Canonical identifier of the agent that produced this event.
                     Must match the agent_id defined in ARCHITECTURE_DEEP.md.

    timestamp      : UTC datetime this event was produced.

    schema_version : Version of this event contract.  Increment on breaking
                     changes to the six required fields.

    payload        : Agent-specific data.  Shape varies by agent; see each
                     agent's module docstring and the fixture files for
                     concrete examples.
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "1.0"
    payload: dict[str, Any]
