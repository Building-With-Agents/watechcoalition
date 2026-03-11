"""Tests for Commit 3 Redis Streams event bus behavior."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus import HandlerExecutionError, RedisStreamsEventBus
from agents.normalization.events import normalization_complete_payload
from agents.tests.message_bus_stream_fixtures import generate_ingest_batches


class _FakeRedisStreamsClient:
    """In-memory Redis Streams subset used for deterministic bus tests."""

    def __init__(self) -> None:
        self._streams: dict[str, list[tuple[str, dict[str, str]]]] = defaultdict(list)
        self._groups: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)

    def xadd(self, name: str, fields: Mapping[str, str], id: str = "*") -> str:
        stream = self._streams[name]
        stream_id = f"{len(stream) + 1}-0" if id == "*" else id
        stream.append((stream_id, dict(fields)))
        return stream_id

    def xgroup_create(
        self,
        name: str,
        groupname: str,
        id: str = "0",
        mkstream: bool = False,
    ) -> bool:
        groups_for_stream = self._groups[name]
        if groupname in groups_for_stream:
            raise RuntimeError("BUSYGROUP Consumer Group name already exists")

        if mkstream and name not in self._streams:
            self._streams[name] = []

        start_index = 0 if id in {"0", "0-0"} else len(self._streams[name])
        groups_for_stream[groupname] = {
            "next_index": start_index,
            "pending": {},
        }
        return True

    def xreadgroup(
        self,
        groupname: str,
        consumername: str,
        streams: Mapping[str, str],
        count: int | None = None,
        block: int | None = None,
    ) -> list[tuple[str, list[tuple[str, dict[str, str]]]]]:
        del block
        if len(streams) != 1:
            raise RuntimeError("fake client only supports one stream at a time")

        stream_name, offset = next(iter(streams.items()))
        stream = self._streams[stream_name]
        group_state = self._groups[stream_name][groupname]
        max_items = count if count is not None else len(stream)
        pending = group_state["pending"]
        assert isinstance(pending, dict)

        if offset == ">":
            start = int(group_state["next_index"])
            selected = stream[start : start + max_items]
            group_state["next_index"] = start + len(selected)
            for stream_id, fields in selected:
                pending[stream_id] = {
                    "consumer": consumername,
                    "fields": fields,
                }
            if not selected:
                return []
            return [(stream_name, [(stream_id, fields) for stream_id, fields in selected])]

        if offset == "0":
            selected: list[tuple[str, dict[str, str]]] = []
            for stream_id, payload in pending.items():
                if payload.get("consumer") != consumername:
                    continue
                fields = payload.get("fields", {})
                if isinstance(fields, dict):
                    selected.append((stream_id, fields))
                if len(selected) >= max_items:
                    break
            if not selected:
                return []
            return [(stream_name, selected)]

        raise RuntimeError(f"unsupported offset '{offset}' for fake client")

    def xack(self, name: str, groupname: str, *ids: str) -> int:
        pending = self._groups[name][groupname]["pending"]
        assert isinstance(pending, dict)
        acked = 0
        for stream_id in ids:
            if stream_id in pending:
                pending.pop(stream_id, None)
                acked += 1
        return acked


def _drain_bus(bus: RedisStreamsEventBus, *, max_iterations: int = 10_000) -> None:
    """Consume until no more pending/new entries are available."""
    for _ in range(max_iterations):
        consumed = bus.consume_available(max_events=256, replay_pending=True)
        if consumed == 0:
            return
    raise AssertionError("bus did not drain within iteration guard")


def test_redis_streams_round_trip_serialization() -> None:
    """Round-trip all envelope fields for contract consistency with in-process bus."""
    event = EventEnvelope(
        correlation_id="corr-1",
        agent_id="ingestion-agent",
        payload={"event_type": "IngestBatch", "batch_id": "batch-1"},
    )

    serialized = RedisStreamsEventBus.serialize_envelope(event)
    decoded = RedisStreamsEventBus.deserialize_envelope(serialized)

    assert decoded.event_id == event.event_id
    assert decoded.correlation_id == event.correlation_id
    assert decoded.agent_id == event.agent_id
    assert decoded.schema_version == event.schema_version
    assert decoded.timestamp == event.timestamp
    assert decoded.payload == event.payload


def test_redis_streams_harness_equivalent_stream_preserves_correlation() -> None:
    bus = RedisStreamsEventBus(
        client=_FakeRedisStreamsClient(),
        stream_name="exp004:redis-test",
        group_name="exp004:redis-group",
        consumer_name="exp004:redis-consumer",
    )
    ingest_events = list(generate_ingest_batches(count=1000, seed=42))
    normalization_seen_correlation_ids: list[str] = []
    emitted_completions: list[EventEnvelope] = []

    def _normalization_handler(event: EventEnvelope) -> None:
        normalization_seen_correlation_ids.append(event.correlation_id)
        completion = EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id="normalization-agent",
            payload=normalization_complete_payload(
                batch_id=str(event.payload.get("batch_id", "")),
                region_id=str(event.payload.get("region_id", "")),
                normalized_count=int(event.payload.get("staged_count", 0)),
                quarantined_count=int(event.payload.get("error_count", 0)),
                normalization_status="success",
            ),
        )
        bus.publish(completion)

    def _completion_handler(event: EventEnvelope) -> None:
        emitted_completions.append(event)

    bus.subscribe(
        "IngestBatch",
        _normalization_handler,
        subscriber_id="normalization-agent",
    )
    bus.subscribe(
        "NormalizationComplete",
        _completion_handler,
        subscriber_id="analytics-agent",
    )

    for event in ingest_events:
        bus.publish(event)

    _drain_bus(bus)

    published_correlation_ids = [event.correlation_id for event in ingest_events]
    completion_correlation_ids = [event.correlation_id for event in emitted_completions]

    assert len(normalization_seen_correlation_ids) == 1000
    assert len(emitted_completions) == 1000
    assert normalization_seen_correlation_ids == published_correlation_ids
    assert completion_correlation_ids == published_correlation_ids
    assert bus.counters == {
        "published_events": 2000,
        "delivered_events": 2000,
        "handler_failures": 0,
        "queue_depth": 0,
        "in_flight": 0,
    }


def test_redis_streams_crash_and_replay_preserves_event_id_set() -> None:
    bus = RedisStreamsEventBus(
        client=_FakeRedisStreamsClient(),
        stream_name="exp004:crash-test",
        group_name="exp004:crash-group",
        consumer_name="exp004:crash-consumer",
    )
    ingest_events = list(generate_ingest_batches(count=1000, seed=42))
    published_event_ids = [event.event_id for event in ingest_events]
    first_run_processed_event_ids: list[str] = []
    replay_processed_event_ids: list[str] = []
    replay_mode = False
    seen = 0

    def _crash_once_handler(event: EventEnvelope) -> None:
        nonlocal seen
        if replay_mode:
            replay_processed_event_ids.append(event.event_id)
            return

        seen += 1
        if seen == 500:
            raise RuntimeError("simulated crash at event index 500")
        first_run_processed_event_ids.append(event.event_id)

    bus.subscribe(
        "IngestBatch",
        _crash_once_handler,
        subscriber_id="normalization-agent",
    )

    for event in ingest_events:
        bus.publish(event)

    crash_triggered = False
    while True:
        try:
            consumed = bus.consume_available(
                max_events=1,
                replay_pending=True,
                stop_on_handler_error=True,
            )
        except HandlerExecutionError:
            crash_triggered = True
            break

        if consumed == 0:
            break

    assert crash_triggered is True
    assert len(first_run_processed_event_ids) == 499

    replay_mode = True
    _drain_bus(bus)

    combined_ids = first_run_processed_event_ids + replay_processed_event_ids
    replay_count = len(replay_processed_event_ids)
    replay_completeness = (len(combined_ids) / len(published_event_ids)) * 100

    assert replay_count == 501
    assert replay_completeness == 100.0
    assert len(combined_ids) == len(published_event_ids)
    assert set(combined_ids) == set(published_event_ids)
    assert bus.counters == {
        "published_events": 1000,
        "delivered_events": 1000,
        "handler_failures": 1,
        "queue_depth": 0,
        "in_flight": 0,
    }
