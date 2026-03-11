"""Kafka event bus candidate for Week 3 Experiment 004."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import Awaitable, Sequence
from inspect import isawaitable
from typing import Protocol, cast

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus.base import EventBusBase
from agents.common.message_bus.contracts import EventHandler, Subscription


class KafkaEventBusError(RuntimeError):
    """Base error for Kafka message bus failures."""


class KafkaDependencyError(KafkaEventBusError):
    """Raised when kafka-python is required but unavailable."""


class KafkaHandlerExecutionError(KafkaEventBusError):
    """Raised when stop_on_handler_error=True and a handler fails."""

    def __init__(
        self,
        *,
        topic: str,
        partition: int,
        offset: int,
        event_type: str,
        subscriber_id: str,
        cause: Exception,
    ) -> None:
        super().__init__(
            f"handler '{subscriber_id}' failed for {topic}[{partition}]@{offset} "
            f"event_type='{event_type}': {cause}"
        )
        self.topic = topic
        self.partition = partition
        self.offset = offset
        self.event_type = event_type
        self.subscriber_id = subscriber_id
        self.cause = cause


class KafkaMessage(Protocol):
    """Minimal consumed Kafka record contract used by KafkaEventBus."""

    topic: str
    partition: int
    offset: int
    value: bytes


class KafkaProducerClient(Protocol):
    """Minimal producer contract used by KafkaEventBus."""

    def send(self, topic: str, value: bytes, *, key: bytes | None = None) -> object:
        """Publish one serialized event payload to a topic."""


class KafkaConsumerClient(Protocol):
    """Minimal consumer contract used by KafkaEventBus."""

    def poll(
        self,
        *,
        timeout_ms: int = 0,
        max_records: int | None = None,
    ) -> Sequence[KafkaMessage]:
        """Read available messages."""

    def commit(self, message: KafkaMessage) -> None:
        """Commit one message offset after successful handling."""

    def seek(self, message: KafkaMessage) -> None:
        """Move read position back to the provided message offset."""


class KafkaEventBus(EventBusBase):
    """Kafka-backed EventBus candidate for transport parity experiments."""

    def __init__(
        self,
        *,
        producer: KafkaProducerClient,
        consumer: KafkaConsumerClient,
        topic: str = "exp004.events",
    ) -> None:
        self._producer = producer
        self._consumer = consumer
        self._topic = topic

        self._subscribers: dict[str, list[tuple[Subscription, EventHandler]]] = (
            defaultdict(list)
        )
        self._published_events = 0
        self._delivered_events = 0
        self._handler_failures = 0
        self._committed_message_ids: set[str] = set()
        self._in_flight_message_ids: set[str] = set()

    @classmethod
    def from_bootstrap_servers(
        cls,
        bootstrap_servers: str | Sequence[str],
        *,
        topic: str = "exp004.events",
        group_id: str = "exp004-group",
        client_id: str = "exp004-consumer",
        auto_offset_reset: str = "earliest",
    ) -> KafkaEventBus:
        """Build KafkaEventBus from kafka-python producer/consumer clients."""
        try:
            from kafka import KafkaConsumer, KafkaProducer
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise KafkaDependencyError(
                "kafka-python is required to construct KafkaEventBus.from_bootstrap_servers"
            ) from exc

        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            acks="all",
            retries=3,
        )
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            client_id=client_id,
            enable_auto_commit=False,
            auto_offset_reset=auto_offset_reset,
        )

        return cls(
            producer=_KafkaPythonProducerAdapter(producer),
            consumer=_KafkaPythonConsumerAdapter(consumer),
            topic=topic,
        )

    @staticmethod
    def serialize_envelope(event: EventEnvelope) -> str:
        """Serialize an EventEnvelope with deterministic key ordering."""
        return json.dumps(
            event.model_dump(mode="json"),
            separators=(",", ":"),
            sort_keys=True,
        )

    @staticmethod
    def deserialize_envelope(raw: str | bytes) -> EventEnvelope:
        """Deserialize a JSON payload string into EventEnvelope."""
        if isinstance(raw, bytes):
            return EventEnvelope.model_validate_json(raw.decode("utf-8"))
        return EventEnvelope.model_validate_json(raw)

    @property
    def counters(self) -> dict[str, int]:
        """Snapshot counters used by Week 3 transport comparisons."""
        return {
            "published_events": self._published_events,
            "delivered_events": self._delivered_events,
            "handler_failures": self._handler_failures,
            "queue_depth": max(
                self._published_events - len(self._committed_message_ids),
                0,
            ),
            "in_flight": len(self._in_flight_message_ids),
        }

    def publish(self, event: EventEnvelope) -> None:
        """Publish one envelope to the configured Kafka topic."""
        self.event_type_for(event)
        payload = self.serialize_envelope(event).encode("utf-8")
        key = event.correlation_id.encode("utf-8") if event.correlation_id else None
        self._producer.send(self._topic, payload, key=key)
        self._published_events += 1

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        *,
        subscriber_id: str,
    ) -> Subscription:
        """Register a handler for one validated event type."""
        subscription = self.validate_subscription(event_type, subscriber_id)
        validated_handler = self.validate_subscription_handler(handler)
        self._subscribers[subscription.event_type].append(
            (subscription, validated_handler)
        )
        return subscription

    def consume_available(
        self,
        *,
        max_events: int = 100,
        timeout_ms: int = 0,
        stop_on_handler_error: bool = False,
    ) -> int:
        """Consume and dispatch up to max_events from the topic."""
        if max_events <= 0:
            return 0

        records = tuple(
            self._consumer.poll(timeout_ms=timeout_ms, max_records=max_events)
        )
        if not records:
            return 0

        total_processed = 0
        for record in records:
            if total_processed >= max_events:
                break

            message_id = _message_id(record)
            self._in_flight_message_ids.add(message_id)
            total_processed += 1

            try:
                should_continue = self._dispatch_record(
                    record=record,
                    message_id=message_id,
                    stop_on_handler_error=stop_on_handler_error,
                )
            except KafkaHandlerExecutionError:
                self._in_flight_message_ids.discard(message_id)
                self._consumer.seek(record)
                raise

            if not should_continue:
                # Keep ordering semantics: do not advance beyond the first failed
                # uncommitted message.
                self._in_flight_message_ids.discard(message_id)
                self._consumer.seek(record)
                break

        return total_processed

    def _dispatch_record(
        self,
        *,
        record: KafkaMessage,
        message_id: str,
        stop_on_handler_error: bool,
    ) -> bool:
        try:
            event = self.deserialize_envelope(record.value)
            event_type = self.event_type_for(event)
        except Exception as exc:
            self._handler_failures += 1
            if stop_on_handler_error:
                raise KafkaHandlerExecutionError(
                    topic=record.topic,
                    partition=record.partition,
                    offset=record.offset,
                    event_type="unknown",
                    subscriber_id="deserializer",
                    cause=exc,
                ) from exc
            return False

        handlers = tuple(self._subscribers.get(event_type, ()))
        if not handlers:
            self._commit(record=record, message_id=message_id)
            return True

        handler_failed = False
        for subscription, handler in handlers:
            try:
                result = handler(event)
                if isawaitable(result):
                    asyncio.run(cast(Awaitable[object], result))
                self._delivered_events += 1
            except Exception as exc:
                handler_failed = True
                self._handler_failures += 1
                if stop_on_handler_error:
                    raise KafkaHandlerExecutionError(
                        topic=record.topic,
                        partition=record.partition,
                        offset=record.offset,
                        event_type=event_type,
                        subscriber_id=subscription.subscriber_id,
                        cause=exc,
                    ) from exc

        if not handler_failed:
            self._commit(record=record, message_id=message_id)
            return True

        return False

    def _commit(self, *, record: KafkaMessage, message_id: str) -> None:
        self._consumer.commit(record)
        self._committed_message_ids.add(message_id)
        self._in_flight_message_ids.discard(message_id)


class _KafkaPythonProducerAdapter:
    """Adapter that makes kafka-python producer match KafkaProducerClient."""

    def __init__(self, producer: object) -> None:
        self._producer = producer

    def send(self, topic: str, value: bytes, *, key: bytes | None = None) -> object:
        send_result = self._producer.send(topic, value=value, key=key)
        # EXP-004 keeps publish semantics synchronous for deterministic counters.
        # Production can swap this for async/callback delivery reporting.
        send_result.get(timeout=10)
        return send_result


class _KafkaPythonConsumerAdapter:
    """Adapter that makes kafka-python consumer match KafkaConsumerClient."""

    def __init__(self, consumer: object) -> None:
        self._consumer = consumer

    def poll(
        self,
        *,
        timeout_ms: int = 0,
        max_records: int | None = None,
    ) -> Sequence[KafkaMessage]:
        polled = self._consumer.poll(timeout_ms=timeout_ms, max_records=max_records)
        flattened: list[KafkaMessage] = []

        for records in polled.values():
            flattened.extend(cast(Sequence[KafkaMessage], records))

        flattened.sort(key=lambda record: (record.topic, record.partition, record.offset))
        return flattened

    def commit(self, message: KafkaMessage) -> None:
        from kafka.structs import OffsetAndMetadata, TopicPartition

        topic_partition = TopicPartition(message.topic, message.partition)
        self._consumer.commit(
            offsets={topic_partition: OffsetAndMetadata(message.offset + 1, "")}
        )

    def seek(self, message: KafkaMessage) -> None:
        from kafka.structs import TopicPartition

        topic_partition = TopicPartition(message.topic, message.partition)
        self._consumer.seek(topic_partition, message.offset)


def _message_id(record: KafkaMessage) -> str:
    return f"{record.topic}:{record.partition}:{record.offset}"
