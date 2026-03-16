"""Tests for synthetic NormalizationComplete, SourceFailure, NormalizationFailed generators."""

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope
from agents.common.events.synthetic_events import (
    generate_synthetic_normalization_complete,
    generate_synthetic_normalization_failed,
    generate_synthetic_source_failures,
)


class TestNormalizationCompleteGenerator:
    """NormalizationComplete generator yields valid EventEnvelopes."""

    def test_each_event_is_event_envelope(self) -> None:
        events = list(generate_synthetic_normalization_complete(count=20, seed=42))
        for event in events:
            assert isinstance(event, EventEnvelope)

    def test_agent_id_and_schema_version(self) -> None:
        events = list(generate_synthetic_normalization_complete(count=10, seed=42))
        for event in events:
            assert event.agent_id == "normalization-agent"
            assert event.schema_version == "1.0"

    def test_payload_has_required_keys(self) -> None:
        required = {
            "event_type",
            "batch_id",
            "region_id",
            "normalized_count",
            "quarantined_count",
            "normalization_status",
        }
        events = list(generate_synthetic_normalization_complete(count=5, seed=42))
        for event in events:
            assert set(event.payload) >= required
            assert event.payload["event_type"] == "NormalizationComplete"

    def test_count(self) -> None:
        events = list(generate_synthetic_normalization_complete(count=100, seed=42))
        assert len(events) == 100

    def test_determinism(self) -> None:
        run1 = list(generate_synthetic_normalization_complete(count=10, seed=42))
        run2 = list(generate_synthetic_normalization_complete(count=10, seed=42))
        assert run1[0].event_id == run2[0].event_id
        assert run1[0].payload == run2[0].payload
        assert run1[-1].event_id == run2[-1].event_id


class TestSourceFailureGenerator:
    """SourceFailure generator yields valid EventEnvelopes."""

    def test_each_event_is_event_envelope(self) -> None:
        events = list(generate_synthetic_source_failures(count=10, seed=42))
        for event in events:
            assert isinstance(event, EventEnvelope)

    def test_agent_id_and_schema_version(self) -> None:
        events = list(generate_synthetic_source_failures(count=5, seed=42))
        for event in events:
            assert event.agent_id == "ingestion-agent"
            assert event.schema_version == "1.0"

    def test_payload_has_required_keys(self) -> None:
        required = {
            "event_type",
            "run_id",
            "source",
            "error",
            "error_type",
            "severity",
            "error_reason",
        }
        events = list(generate_synthetic_source_failures(count=5, seed=42))
        for event in events:
            assert set(event.payload) >= required
            assert event.payload["event_type"] == "SourceFailure"
            assert event.payload["severity"] == "critical"

    def test_count(self) -> None:
        events = list(generate_synthetic_source_failures(count=10, seed=42))
        assert len(events) == 10

    def test_determinism(self) -> None:
        run1 = list(generate_synthetic_source_failures(count=5, seed=42))
        run2 = list(generate_synthetic_source_failures(count=5, seed=42))
        assert run1[0].event_id == run2[0].event_id
        assert run1[0].payload == run2[0].payload


class TestNormalizationFailedGenerator:
    """NormalizationFailed generator yields valid EventEnvelopes."""

    def test_each_event_is_event_envelope(self) -> None:
        events = list(generate_synthetic_normalization_failed(count=10, seed=42))
        for event in events:
            assert isinstance(event, EventEnvelope)

    def test_agent_id_and_schema_version(self) -> None:
        events = list(generate_synthetic_normalization_failed(count=5, seed=42))
        for event in events:
            assert event.agent_id == "normalization-agent"
            assert event.schema_version == "1.0"

    def test_payload_has_required_keys(self) -> None:
        required = {
            "event_type",
            "batch_id",
            "error",
            "error_type",
            "severity",
            "error_reason",
        }
        events = list(generate_synthetic_normalization_failed(count=5, seed=42))
        for event in events:
            assert set(event.payload) >= required
            assert event.payload["event_type"] == "NormalizationFailed"
            assert event.payload["severity"] == "critical"

    def test_count(self) -> None:
        events = list(generate_synthetic_normalization_failed(count=10, seed=42))
        assert len(events) == 10

    def test_determinism(self) -> None:
        run1 = list(generate_synthetic_normalization_failed(count=5, seed=42))
        run2 = list(generate_synthetic_normalization_failed(count=5, seed=42))
        assert run1[0].event_id == run2[0].event_id
        assert run1[0].payload == run2[0].payload
