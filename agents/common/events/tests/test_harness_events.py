"""Harness structure tests for EXP-004 synthetic IngestBatch generator.

Validates only the harness output: envelope shape, payload shape, count,
determinism, and uniqueness. No bus, throughput, crash, or replay tests.
"""

from __future__ import annotations

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.common.events.ingest_batch_harness import (
    assert_valid_ingest_batch_envelope,
    generate_synthetic_ingest_batches,
    is_valid_ingest_batch_envelope,
)


class TestHarnessEnvelopeShape:
    """Every yielded item is a valid EventEnvelope with required fields set."""

    def test_each_event_is_event_envelope(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=1000, seed=42))
        for event in events:
            assert isinstance(event, EventEnvelope)

    def test_agent_id_and_schema_version(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=1000, seed=42))
        for event in events:
            assert event.agent_id == "ingestion_agent"
            assert event.schema_version == "1.0"

    def test_correlation_id_and_event_id_and_timestamp_set(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=100, seed=42))
        for event in events:
            assert event.correlation_id
            assert event.event_id
            assert event.timestamp is not None


class TestHarnessPayloadShape:
    """Every event.payload has all IngestBatch keys and correct types."""

    def test_assert_valid_passes_for_all_events(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=1000, seed=42))
        for event in events:
            assert_valid_ingest_batch_envelope(event)

    def test_first_last_middle_pass_validation(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=1000, seed=42))
        for idx in (0, 499, 999):
            assert is_valid_ingest_batch_envelope(events[idx])

    def test_payload_has_ingest_batch_keys(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=10, seed=42))
        required = {"event_type", "batch_id", "source", "region_id",
                    "total_fetched", "staged_count", "dedup_count", "error_count"}
        for event in events:
            assert set(event.payload) >= required
            assert event.payload["event_type"] == "IngestBatch"


class TestHarnessCount:
    """Exactly count events are yielded."""

    def test_default_count_is_1000(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=1000, seed=42))
        assert len(events) == 1000

    def test_custom_count(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=50, seed=1))
        assert len(events) == 50


class TestHarnessDeterminism:
    """Same seed produces the same events in the same order."""

    def test_same_seed_same_events(self) -> None:
        run1 = list(generate_synthetic_ingest_batches(count=1000, seed=42))
        run2 = list(generate_synthetic_ingest_batches(count=1000, seed=42))
        assert len(run1) == len(run2) == 1000
        assert run1[0].event_id == run2[0].event_id
        assert run1[0].payload["batch_id"] == run2[0].payload["batch_id"]
        assert run1[0].payload == run2[0].payload
        assert run1[999].event_id == run2[999].event_id
        assert run1[999].payload["batch_id"] == run2[999].payload["batch_id"]
        assert run1[999].payload == run2[999].payload

    def test_different_seed_different_events(self) -> None:
        run1 = list(generate_synthetic_ingest_batches(count=10, seed=1))
        run2 = list(generate_synthetic_ingest_batches(count=10, seed=2))
        assert run1[0].event_id != run2[0].event_id
        assert run1[0].payload["batch_id"] != run2[0].payload["batch_id"]


class TestHarnessUniqueness:
    """No duplicate event_id in the generated events."""

    def test_no_duplicate_event_ids(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=1000, seed=42))
        ids = [e.event_id for e in events]
        assert len(set(ids)) == 1000


class TestValidationHelperBadStructure:
    """assert_valid_ingest_batch_envelope rejects invalid envelope/payload."""

    def test_valid_event_does_not_raise(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=1, seed=42))
        assert_valid_ingest_batch_envelope(events[0])

    def test_valid_event_returns_true(self) -> None:
        events = list(generate_synthetic_ingest_batches(count=1, seed=42))
        assert is_valid_ingest_batch_envelope(events[0]) is True

    def test_missing_payload_key_raises(self) -> None:
        event = EventEnvelope(
            correlation_id="c1",
            agent_id="ingestion_agent",
            payload={
                "event_type": "IngestBatch",
                "batch_id": "b1",
                "source": "s",
                "region_id": "us",
                "total_fetched": 10,
                "staged_count": 10,
                "dedup_count": 0,
                # missing error_count
            },
        )
        with pytest.raises(ValueError, match="missing required keys"):
            assert_valid_ingest_batch_envelope(event)
        assert is_valid_ingest_batch_envelope(event) is False

    def test_wrong_payload_type_raises(self) -> None:
        event = EventEnvelope(
            correlation_id="c1",
            agent_id="ingestion_agent",
            payload={
                "event_type": "IngestBatch",
                "batch_id": "b1",
                "source": "s",
                "region_id": "us",
                "total_fetched": "not-an-int",  # wrong type
                "staged_count": 10,
                "dedup_count": 0,
                "error_count": 0,
            },
        )
        with pytest.raises(ValueError, match="must be int"):
            assert_valid_ingest_batch_envelope(event)
        assert is_valid_ingest_batch_envelope(event) is False

    def test_wrong_event_type_raises(self) -> None:
        event = EventEnvelope(
            correlation_id="c1",
            agent_id="ingestion_agent",
            payload={
                "event_type": "OtherEvent",
                "batch_id": "b1",
                "source": "s",
                "region_id": "us",
                "total_fetched": 10,
                "staged_count": 10,
                "dedup_count": 0,
                "error_count": 0,
            },
        )
        with pytest.raises(ValueError, match="must be 'IngestBatch'"):
            assert_valid_ingest_batch_envelope(event)
        assert is_valid_ingest_batch_envelope(event) is False
