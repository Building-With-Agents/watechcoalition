"""Candidate builders for transport comparison runs."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from agents.common.message_bus.comparison import TransportCandidate
from agents.common.message_bus.in_process import InProcessEventBus
from agents.common.message_bus.kafka import KafkaEventBus
from agents.common.message_bus.redis_streams import RedisStreamsEventBus


class FakeRedisStreamsClient:
    """In-memory Redis Streams subset for deterministic comparisons."""

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
            return [(stream_name, list(selected))]

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


@dataclass(frozen=True)
class FakeKafkaRecord:
    """Minimal consumed record shape for fake Kafka comparisons."""

    topic: str
    partition: int
    offset: int
    value: bytes
    key: bytes | None = None


class FakeKafkaBroker:
    """In-memory topic storage shared by fake producer and consumer clients."""

    def __init__(self) -> None:
        self._topics: dict[str, list[FakeKafkaRecord]] = defaultdict(list)

    def append(self, topic: str, value: bytes, *, key: bytes | None = None) -> FakeKafkaRecord:
        stream = self._topics[topic]
        record = FakeKafkaRecord(
            topic=topic,
            partition=0,
            offset=len(stream),
            value=value,
            key=key,
        )
        stream.append(record)
        return record

    def read(self, topic: str, offset: int, limit: int) -> Sequence[FakeKafkaRecord]:
        if limit <= 0:
            return []
        return self._topics[topic][offset : offset + limit]


class FakeKafkaProducer:
    """In-memory producer used for deterministic Kafka comparisons."""

    def __init__(self, broker: FakeKafkaBroker) -> None:
        self._broker = broker

    def send(self, topic: str, value: bytes, *, key: bytes | None = None) -> FakeKafkaRecord:
        return self._broker.append(topic, value, key=key)


class FakeKafkaConsumer:
    """In-memory consumer with poll/commit/seek semantics."""

    def __init__(self, broker: FakeKafkaBroker, *, topic: str) -> None:
        self._broker = broker
        self._topic = topic
        self._next_offset = 0
        self._committed_offset = 0

    def poll(
        self,
        *,
        timeout_ms: int = 0,
        max_records: int | None = None,
    ) -> Sequence[FakeKafkaRecord]:
        del timeout_ms
        limit = max_records if max_records is not None else 1
        records = self._broker.read(self._topic, self._next_offset, limit)
        self._next_offset += len(records)
        return records

    def commit(self, message: FakeKafkaRecord) -> None:
        self._committed_offset = max(self._committed_offset, message.offset + 1)

    def seek(self, message: FakeKafkaRecord) -> None:
        self._next_offset = message.offset


def build_in_process_candidate() -> TransportCandidate:
    """Build the baseline in-process transport candidate."""
    return TransportCandidate(
        transport="in_process",
        backend="in_memory",
        factory=InProcessEventBus,
    )


def build_fake_redis_candidate(
    *,
    stream_name: str = "exp004:compare-redis",
    group_name: str = "exp004:compare-redis-group",
    consumer_name: str = "exp004:compare-redis-consumer",
) -> TransportCandidate:
    """Build the fake Redis Streams comparison candidate."""
    return TransportCandidate(
        transport="redis_streams",
        backend="fake_redis",
        factory=lambda: RedisStreamsEventBus(
            client=FakeRedisStreamsClient(),
            stream_name=stream_name,
            group_name=group_name,
            consumer_name=consumer_name,
        ),
    )


def build_live_redis_candidate(
    redis_url: str,
    *,
    stream_name: str = "exp004:events",
    group_name: str = "exp004-group",
    consumer_name: str = "exp004-consumer",
    group_start_id: str = "0",
) -> TransportCandidate:
    """Build a live Redis Streams comparison candidate."""
    return TransportCandidate(
        transport="redis_streams",
        backend="real_redis",
        factory=lambda: RedisStreamsEventBus.from_url(
            redis_url,
            stream_name=stream_name,
            group_name=group_name,
            consumer_name=consumer_name,
            group_start_id=group_start_id,
        ),
    )


def build_fake_kafka_candidate(
    *,
    topic: str = "exp004:compare-kafka",
) -> TransportCandidate:
    """Build the fake Kafka comparison candidate."""
    return TransportCandidate(
        transport="kafka",
        backend="fake_kafka",
        factory=lambda: _build_fake_kafka_bus(topic=topic),
    )


def build_live_kafka_candidate(
    bootstrap_servers: str | Sequence[str],
    *,
    topic: str = "exp004.events",
    group_id: str = "exp004-group",
    client_id: str = "exp004-consumer",
    auto_offset_reset: str = "earliest",
) -> TransportCandidate:
    """Build a live Kafka comparison candidate."""
    return TransportCandidate(
        transport="kafka",
        backend="real_kafka",
        factory=lambda: KafkaEventBus.from_bootstrap_servers(
            bootstrap_servers,
            topic=topic,
            group_id=group_id,
            client_id=client_id,
            auto_offset_reset=auto_offset_reset,
        ),
    )


def build_transport_candidates(
    *,
    redis_url: str | None = None,
    kafka_bootstrap_servers: str | Sequence[str] | None = None,
    redis_stream_name: str = "exp004:events",
    redis_group_name: str = "exp004-group",
    redis_consumer_name: str = "exp004-consumer",
    kafka_topic: str = "exp004.events",
    kafka_group_id: str = "exp004-group",
    kafka_client_id: str = "exp004-consumer",
    kafka_auto_offset_reset: str = "earliest",
) -> list[TransportCandidate]:
    """Build the default three-way candidate list for the comparison CLI."""
    candidates = [build_in_process_candidate()]

    if redis_url:
        candidates.append(
            build_live_redis_candidate(
                redis_url,
                stream_name=redis_stream_name,
                group_name=redis_group_name,
                consumer_name=redis_consumer_name,
            )
        )
    else:
        candidates.append(
            build_fake_redis_candidate(
                stream_name=redis_stream_name.replace(".", "-"),
                group_name=redis_group_name.replace(".", "-"),
                consumer_name=redis_consumer_name.replace(".", "-"),
            )
        )

    if kafka_bootstrap_servers:
        candidates.append(
            build_live_kafka_candidate(
                kafka_bootstrap_servers,
                topic=kafka_topic,
                group_id=kafka_group_id,
                client_id=kafka_client_id,
                auto_offset_reset=kafka_auto_offset_reset,
            )
        )
    else:
        candidates.append(build_fake_kafka_candidate(topic=kafka_topic.replace(".", ":")))

    return candidates


def _build_fake_kafka_bus(*, topic: str) -> KafkaEventBus:
    broker = FakeKafkaBroker()
    return KafkaEventBus(
        producer=FakeKafkaProducer(broker),
        consumer=FakeKafkaConsumer(broker, topic=topic),
        topic=topic,
    )


__all__ = [
    "FakeKafkaBroker",
    "FakeKafkaConsumer",
    "FakeKafkaProducer",
    "FakeKafkaRecord",
    "FakeRedisStreamsClient",
    "build_fake_kafka_candidate",
    "build_fake_redis_candidate",
    "build_in_process_candidate",
    "build_live_kafka_candidate",
    "build_live_redis_candidate",
    "build_transport_candidates",
]
