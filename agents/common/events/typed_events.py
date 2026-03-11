"""
Typed event classes for EXP-004 — wrapper around EventEnvelope for type hints and pattern matching.

Each event type has a distinct class that validates payload["event_type"] and exposes
the envelope. Serialization (model_dump) matches EventEnvelope + payload for bus compatibility.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator

from agents.common.event_envelope import EventEnvelope


class IngestBatchEvent(BaseModel):
    """Typed wrapper for IngestBatch events."""

    envelope: EventEnvelope

    @field_validator("envelope")
    @classmethod
    def check_event_type(cls, v: EventEnvelope) -> EventEnvelope:
        if v.payload.get("event_type") != "IngestBatch":
            raise ValueError(
                f"Expected payload event_type 'IngestBatch', got {v.payload.get('event_type')!r}"
            )
        return v

    @property
    def correlation_id(self) -> str:
        return self.envelope.correlation_id

    @property
    def batch_id(self) -> str:
        return self.envelope.payload["batch_id"]

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize as EventEnvelope so bus/callers get same shape."""
        return self.envelope.model_dump(**kwargs)


class NormalizationCompleteEvent(BaseModel):
    """Typed wrapper for NormalizationComplete events."""

    envelope: EventEnvelope

    @field_validator("envelope")
    @classmethod
    def check_event_type(cls, v: EventEnvelope) -> EventEnvelope:
        if v.payload.get("event_type") != "NormalizationComplete":
            raise ValueError(
                f"Expected payload event_type 'NormalizationComplete', got {v.payload.get('event_type')!r}"
            )
        return v

    @property
    def correlation_id(self) -> str:
        return self.envelope.correlation_id

    @property
    def batch_id(self) -> str:
        return self.envelope.payload["batch_id"]

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        return self.envelope.model_dump(**kwargs)


class SourceFailureEvent(BaseModel):
    """Typed wrapper for SourceFailure events."""

    envelope: EventEnvelope

    @field_validator("envelope")
    @classmethod
    def check_event_type(cls, v: EventEnvelope) -> EventEnvelope:
        if v.payload.get("event_type") != "SourceFailure":
            raise ValueError(
                f"Expected payload event_type 'SourceFailure', got {v.payload.get('event_type')!r}"
            )
        return v

    @property
    def correlation_id(self) -> str:
        return self.envelope.correlation_id

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        return self.envelope.model_dump(**kwargs)


class NormalizationFailedEvent(BaseModel):
    """Typed wrapper for NormalizationFailed events."""

    envelope: EventEnvelope

    @field_validator("envelope")
    @classmethod
    def check_event_type(cls, v: EventEnvelope) -> EventEnvelope:
        if v.payload.get("event_type") != "NormalizationFailed":
            raise ValueError(
                f"Expected payload event_type 'NormalizationFailed', got {v.payload.get('event_type')!r}"
            )
        return v

    @property
    def correlation_id(self) -> str:
        return self.envelope.correlation_id

    @property
    def batch_id(self) -> str:
        return self.envelope.payload["batch_id"]

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        return self.envelope.model_dump(**kwargs)
