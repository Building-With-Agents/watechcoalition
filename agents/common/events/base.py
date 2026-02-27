# agents/common/events/base.py
"""Canonical event envelope for all inter-agent communication."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentEvent:
    """Every inter-agent event must use this shape."""

    event_id: str  # uuid4
    correlation_id: str  # propagated unchanged from IngestBatch through all downstream events
    agent_id: str  # e.g. "ingestion_agent"
    timestamp: datetime
    schema_version: str  # "1.0" — increment on breaking payload changes
    payload: dict
