"""
EXP-004 synthetic event generators for NormalizationComplete, SourceFailure, NormalizationFailed.

Deterministic generators for event-bus tests. Uses same determinism pattern as
ingest_batch_harness: fixed seed, uuid5 for event_id, base timestamp + index.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta

from agents.common.event_envelope import EventEnvelope
from agents.common.events.typed_events import (
    NormalizationCompleteEvent,
    NormalizationFailedEvent,
    SourceFailureEvent,
)
from agents.ingestion.events import source_failure_payload
from agents.normalization.events import (
    normalization_complete_payload,
    normalization_failed_payload,
)

_BASE_TS = datetime(2025, 1, 1, 0, 0, 0)


def generate_synthetic_normalization_complete(
    count: int = 100,
    seed: int = 42,
    typed: bool = False,
) -> Iterator[EventEnvelope | NormalizationCompleteEvent]:
    """
    Yield deterministic NormalizationComplete events.

    Same (count, seed) always produces the same events in the same order.
    When typed=True, yields NormalizationCompleteEvent wrappers; otherwise EventEnvelope.
    """
    correlation_id = f"harness-norm-{seed}"
    for i in range(count):
        event_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS, f"harness-NormalizationComplete-{seed}-{i}"
            )
        )
        timestamp = _BASE_TS + timedelta(seconds=i)
        batch_id = f"harness-norm-batch-{seed}-{i}"
        normalized_count = (seed + i) % 50 + 1
        quarantined_count = (seed + i) % 5
        statuses = ("success", "partial", "complete")
        normalization_status = statuses[(seed + i) % len(statuses)]
        payload = normalization_complete_payload(
            batch_id=batch_id,
            region_id="us",
            normalized_count=normalized_count,
            quarantined_count=quarantined_count,
            normalization_status=normalization_status,
        )
        envelope = EventEnvelope(
            event_id=event_id,
            correlation_id=correlation_id,
            agent_id="normalization-agent",
            timestamp=timestamp,
            schema_version="1.0",
            payload=payload,
        )
        if typed:
            yield NormalizationCompleteEvent(envelope=envelope)
        else:
            yield envelope


def generate_synthetic_source_failures(
    count: int = 10,
    seed: int = 42,
    typed: bool = False,
) -> Iterator[EventEnvelope | SourceFailureEvent]:
    """
    Yield deterministic SourceFailure events.

    Same (count, seed) always produces the same events in the same order.
    When typed=True, yields SourceFailureEvent wrappers; otherwise EventEnvelope.
    """
    correlation_id = f"harness-fail-{seed}"
    sources = ("jsearch", "crawl4ai", "harness")
    for i in range(count):
        event_id = str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"harness-SourceFailure-{seed}-{i}")
        )
        timestamp = _BASE_TS + timedelta(seconds=i)
        run_id = f"harness-run-{seed}-{i}"
        source = sources[i % len(sources)]
        error = f"simulated failure {seed}-{i}"
        error_type = "ConnectionError" if i % 2 == 0 else "TimeoutError"
        error_reason = f"source {source} unreachable (seed={seed}, i={i})"
        payload = source_failure_payload(
            run_id=run_id,
            source=source,
            error=error,
            error_type=error_type,
            severity="critical",
            error_reason=error_reason,
        )
        envelope = EventEnvelope(
            event_id=event_id,
            correlation_id=correlation_id,
            agent_id="ingestion-agent",
            timestamp=timestamp,
            schema_version="1.0",
            payload=payload,
        )
        if typed:
            yield SourceFailureEvent(envelope=envelope)
        else:
            yield envelope


def generate_synthetic_normalization_failed(
    count: int = 10,
    seed: int = 42,
    typed: bool = False,
) -> Iterator[EventEnvelope | NormalizationFailedEvent]:
    """
    Yield deterministic NormalizationFailed events.

    Same (count, seed) always produces the same events in the same order.
    When typed=True, yields NormalizationFailedEvent wrappers; otherwise EventEnvelope.
    """
    correlation_id = f"harness-normfail-{seed}"
    for i in range(count):
        event_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS, f"harness-NormalizationFailed-{seed}-{i}"
            )
        )
        timestamp = _BASE_TS + timedelta(seconds=i)
        batch_id = f"harness-normfail-batch-{seed}-{i}"
        error = f"normalization failed (seed={seed}, i={i})"
        error_type = "SchemaViolation" if i % 2 == 0 else "ValidationError"
        error_reason = f"batch {batch_id} validation failed"
        payload = normalization_failed_payload(
            batch_id=batch_id,
            error=error,
            error_type=error_type,
            severity="critical",
            error_reason=error_reason,
        )
        envelope = EventEnvelope(
            event_id=event_id,
            correlation_id=correlation_id,
            agent_id="normalization-agent",
            timestamp=timestamp,
            schema_version="1.0",
            payload=payload,
        )
        if typed:
            yield NormalizationFailedEvent(envelope=envelope)
        else:
            yield envelope
