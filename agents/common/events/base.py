"""
Event envelope and type constants for the agent pipeline.

All inter-agent events use AgentEvent. See docs/planning/PIPELINE_DESIGN.md
and docs/planning/ARCHITECTURE_DEEP.md.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid


# Schema version for the event envelope; increment on breaking payload changes.
SCHEMA_VERSION = "1.0"


# Event type names (payload semantics are defined per type in the event catalog).
EVENT_INGEST_BATCH = "IngestBatch"
EVENT_NORMALIZATION_COMPLETE = "NormalizationComplete"
EVENT_SKILLS_EXTRACTED = "SkillsExtracted"
EVENT_RECORD_ENRICHED = "RecordEnriched"
EVENT_ANALYTICS_REFRESHED = "AnalyticsRefreshed"
EVENT_RENDER_COMPLETE = "RenderComplete"
EVENT_DEMAND_SIGNALS_UPDATED = "DemandSignalsUpdated"


@dataclass(frozen=True)
class AgentEvent:
    """
    Envelope for every event passed between agents and to the Journey dashboard.
    All fields must be JSON-serializable; no PII in payload when logging.
    """

    event_id: str
    correlation_id: str
    agent_id: str
    timestamp: datetime
    schema_version: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict; timestamp as ISO 8601 string."""
        return {
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "schema_version": self.schema_version,
            "payload": self.payload,
        }


def create_event(
    correlation_id: str,
    agent_id: str,
    schema_version: str,
    payload: dict[str, Any],
) -> AgentEvent:
    """Build an AgentEvent with a new event_id and current UTC timestamp."""
    return AgentEvent(
        event_id=uuid.uuid4().hex,
        correlation_id=correlation_id,
        agent_id=agent_id,
        timestamp=datetime.now(timezone.utc),
        schema_version=schema_version,
        payload=payload,
    )
