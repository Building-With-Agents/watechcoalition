"""Redis Streams event bus candidate for Week 3 Experiment 004."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import Awaitable, Mapping, Sequence
from inspect import isawaitable
from typing import Protocol, cast

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus.base import EventBusBase
from agents.common.message_bus.contracts import EventHandler, Subscription

_EVENT_FIELD = "event"


class RedisStreamsError(RuntimeError):
    """Base error for Redis Streams message bus failures."""


class RedisDependencyError(RedisStreamsError):
    """Raised when redis-py is required but unavailable."""


class HandlerExecutionError(RedisStreamsError):
    """Raised when stop_on_handler_error=True and a handler fails."""

    def __init__(
        self,
        *,
        stream_id: str,
        event_type: str,
        subscriber_id: str,
        cause: Exception,
    ) -> None:
        super().__init__(
            f"handler '{subscriber_id}' failed for stream_id='{stream_id}' "
            f"event_type='{event_type}': {cause}"
        )
        self.stream_id = stream_id
        self.event_type = event_type
        self.subscriber_id = subscriber_id
        self.cause = cause


class RedisStreamsClient(Protocol):
    """Minimal Redis Streams client contract used by RedisStreamsEventBus."""

    def xadd(self, name: str, fields: Mapping[str, str], id: str = "*") -> str | bytes:
        """Append one message to a stream."""

    def xgroup_create(
        self,
        name: str,
        groupname: str,
        id: str = "0",
        mkstream: bool = False,
    ) -> object:
        """Create a consumer group for a stream."""

    def xreadgroup(
        self,
        groupname: str,
        consumername: str,
        streams: Mapping[str, str],
        count: int | None = None,
        block: int | None = None,
    ) -> (
        list[tuple[str | bytes, list[tuple[str | bytes, dict[str | bytes, str | bytes]]]]]
        | None
    ):
        """Read stream entries from a consumer group."""

    def xack(self, name: str, groupname: str, *ids: str) -> int:
        """Acknowledge one or more stream entries."""


class RedisStreamsEventBus(EventBusBase):
    """Redis Streams-backed EventBus candidate for transport parity experiments."""

    def __init__(
        self,
        *,
        client: RedisStreamsClient,
        stream_name: str = "exp004:events",
        group_name: str = "exp004-group",
        consumer_name: str = "exp004-consumer",
        group_start_id: str = "0",
    ) -> None:
        self._client = client
        self._stream_name = stream_name
        self._group_name = group_name
        self._consumer_name = consumer_name
        self._group_start_id = group_start_id

        self._subscribers: dict[str, list[tuple[Subscription, EventHandler]]] = (
            defaultdict(list)
        )
        self._published_events = 0
        self._delivered_events = 0
        self._handler_failures = 0
        self._known_stream_ids: set[str] = set()
        self._acked_stream_ids: set[str] = set()
        self._in_flight_stream_ids: set[str] = set()
        self._max_queue_depth_seen: int = 0
        self._max_in_flight_seen: int = 0

        self._ensure_consumer_group()

    @classmethod
    def from_url(
        cls,
        redis_url: str,
        *,
        stream_name: str = "exp004:events",
        group_name: str = "exp004-group",
        consumer_name: str = "exp004-consumer",
        group_start_id: str = "0",
    ) -> RedisStreamsEventBus:
        """Build a RedisStreamsEventBus using a redis-py client from URL."""
        try:
            import redis
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise RedisDependencyError(
                "redis-py is required to construct RedisStreamsEventBus.from_url"
            ) from exc

        client = redis.Redis.from_url(redis_url)
        return cls(
            client=cast(RedisStreamsClient, client),
            stream_name=stream_name,
            group_name=group_name,
            consumer_name=consumer_name,
            group_start_id=group_start_id,
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

    def _update_peak_counters(self) -> None:
        """Update peak queue_depth and in_flight from current state."""
        current_qd = max(len(self._known_stream_ids) - len(self._acked_stream_ids), 0)
        current_if = len(self._in_flight_stream_ids)
        self._max_queue_depth_seen = max(self._max_queue_depth_seen, current_qd)
        self._max_in_flight_seen = max(self._max_in_flight_seen, current_if)

    @property
    def counters(self) -> dict[str, int]:
        """Snapshot counters used by Week 3 transport comparisons."""
        qd = max(len(self._known_stream_ids) - len(self._acked_stream_ids), 0)
        if_ = len(self._in_flight_stream_ids)
        return {
            "published_events": self._published_events,
            "delivered_events": self._delivered_events,
            "handler_failures": self._handler_failures,
            "queue_depth": qd,
            "in_flight": if_,
            "max_queue_depth_seen": self._max_queue_depth_seen,
            "max_in_flight_seen": self._max_in_flight_seen,
        }

    def publish(self, event: EventEnvelope) -> None:
        """Publish one envelope to the configured Redis stream."""
        self.event_type_for(event)
        payload = self.serialize_envelope(event)
        stream_id = _to_text(self._client.xadd(self._stream_name, {_EVENT_FIELD: payload}))
        self._known_stream_ids.add(stream_id)
        self._published_events += 1
        self._update_peak_counters()

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
        block_ms: int = 0,
        replay_pending: bool = True,
        stop_on_handler_error: bool = False,
    ) -> int:
        """Consume and dispatch up to max_events from pending and new entries."""
        if max_events <= 0:
            return 0

        total_processed = 0
        remaining = max_events
        read_plan: Sequence[str] = ("0", ">") if replay_pending else (">",)

        for offset in read_plan:
            if remaining <= 0:
                break

            entries = self._read_entries(
                offset=offset,
                count=remaining,
                block_ms=block_ms if offset == ">" else 0,
            )
            if not entries:
                continue

            for stream_id, fields in entries:
                self._in_flight_stream_ids.add(stream_id)
                self._update_peak_counters()
                total_processed += 1
                remaining -= 1

                self._dispatch_entry(
                    stream_id=stream_id,
                    fields=fields,
                    stop_on_handler_error=stop_on_handler_error,
                )
                if remaining <= 0:
                    break

        return total_processed

    def _ensure_consumer_group(self) -> None:
        try:
            self._client.xgroup_create(
                self._stream_name,
                self._group_name,
                id=self._group_start_id,
                mkstream=True,
            )
        except Exception as exc:
            message = str(exc)
            if "BUSYGROUP" in message:
                return
            raise RedisStreamsError(
                f"failed to create or access consumer group '{self._group_name}'"
            ) from exc

    def _read_entries(
        self,
        *,
        offset: str,
        count: int,
        block_ms: int,
    ) -> list[tuple[str, dict[str, str]]]:
        raw_response = self._client.xreadgroup(
            self._group_name,
            self._consumer_name,
            {self._stream_name: offset},
            count=count,
            block=block_ms,
        )
        entries: list[tuple[str, dict[str, str]]] = []

        if not raw_response:
            return entries

        for _, stream_entries in raw_response:
            for stream_id, fields in stream_entries:
                normalized_fields = {
                    _to_text(field_name): _to_text(field_value)
                    for field_name, field_value in fields.items()
                }
                entries.append((_to_text(stream_id), normalized_fields))

        return entries

    def _dispatch_entry(
        self,
        *,
        stream_id: str,
        fields: Mapping[str, str],
        stop_on_handler_error: bool,
    ) -> None:
        raw_event = fields.get(_EVENT_FIELD)
        if raw_event is None:
            self._handler_failures += 1
            if stop_on_handler_error:
                raise HandlerExecutionError(
                    stream_id=stream_id,
                    event_type="unknown",
                    subscriber_id="unknown",
                    cause=ValueError(f"missing '{_EVENT_FIELD}' field"),
                )
            return

        try:
            event = self.deserialize_envelope(raw_event)
            event_type = self.event_type_for(event)
        except Exception as exc:
            self._handler_failures += 1
            if stop_on_handler_error:
                raise HandlerExecutionError(
                    stream_id=stream_id,
                    event_type="unknown",
                    subscriber_id="deserializer",
                    cause=exc,
                ) from exc
            return
        handlers = tuple(self._subscribers.get(event_type, ()))

        if not handlers:
            self._ack(stream_id)
            return

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
                    raise HandlerExecutionError(
                        stream_id=stream_id,
                        event_type=event_type,
                        subscriber_id=subscription.subscriber_id,
                        cause=exc,
                    ) from exc

        if not handler_failed:
            self._ack(stream_id)

    def _ack(self, stream_id: str) -> None:
        self._client.xack(self._stream_name, self._group_name, stream_id)
        self._acked_stream_ids.add(stream_id)
        self._in_flight_stream_ids.discard(stream_id)
        self._update_peak_counters()


def _to_text(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, str):
        return value
    return str(value)
