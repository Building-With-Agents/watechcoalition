from __future__ import annotations

"""
Typed event models for the Job Intelligence Engine.

These classes provide structured payloads on top of the shared EventEnvelope
contract defined in `agents/common/event_envelope.py`. All events inherit from
EventEnvelope, and schema_version always defaults to "1.0" — callers never
override it manually.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from agents.common.event_envelope import EventEnvelope


class IngestBatchPayload(BaseModel):
    """
    Payload for a successful IngestBatch event emitted by the Ingestion Agent.
    """

    batch_id: str
    record_count: int
    dedup_count: int
    source: str
    correlation_id: str


class IngestBatch(EventEnvelope):
    """
    IngestBatch event envelope produced by the Ingestion Agent.

    The payload field is typed as IngestBatchPayload. The schema_version
    field always defaults to "1.0".
    """

    payload: IngestBatchPayload
    schema_version: str = Field(default="1.0", frozen=True)


class NormalizationCompletePayload(BaseModel):
    """
    Payload for a successful NormalizationComplete event emitted by the
    Normalization Agent.
    """

    batch_id: str
    valid_count: int
    quarantine_count: int
    correlation_id: str


class NormalizationComplete(EventEnvelope):
    """
    NormalizationComplete event envelope produced by the Normalization Agent.

    The payload field is typed as NormalizationCompletePayload. The
    schema_version field always defaults to "1.0".
    """

    payload: NormalizationCompletePayload
    schema_version: str = Field(default="1.0", frozen=True)


class FailurePayload(BaseModel):
    """
    Base payload for failure events.

    Concrete failure events (SourceFailure, NormalizationFailed) embed
    the error classification and message. Severity defaults to "critical"
    to align with orchestration alerting tiers.
    """

    correlation_id: str
    agent_id: str
    error_type: str
    severity: str = "critical"
    error_reason: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)


class SourceFailure(EventEnvelope):
    """
    SourceFailure event envelope emitted when an ingestion source is
    unavailable after retries.

    The correlation_id and agent_id are carried at the envelope level and
    duplicated in the payload for convenience when events are inspected
    outside the Python type system.
    """

    payload: FailurePayload
    schema_version: str = Field(default="1.0", frozen=True)


class NormalizationFailed(EventEnvelope):
    """
    NormalizationFailed event envelope emitted when a normalization batch
    fails catastrophically.

    The correlation_id and agent_id are carried at the envelope level and
    duplicated in the payload for convenience when events are inspected
    outside the Python type system.
    """

    payload: FailurePayload
    schema_version: str = Field(default="1.0", frozen=True)


__all__ = [
    "IngestBatchPayload",
    "IngestBatch",
    "NormalizationCompletePayload",
    "NormalizationComplete",
    "FailurePayload",
    "SourceFailure",
    "NormalizationFailed",
]

