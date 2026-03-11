"""Shared deterministic ingest stream fixtures for message bus transport tests."""

from __future__ import annotations

import random
from collections.abc import Iterable

from agents.common.event_envelope import EventEnvelope
from agents.ingestion.events import ingest_batch_payload

try:
    from agents.common.events.ingest_batch_harness import (  # pragma: no cover
        generate_synthetic_ingest_batches as _harness_generator,
    )
except ImportError:  # pragma: no cover
    _harness_generator = None


def fixture_synthetic_ingest_batches(
    *, count: int = 1000, seed: int = 42
) -> Iterable[EventEnvelope]:
    """Deterministic fallback stream until Emilio's shared harness lands."""
    rng = random.Random(seed)

    for index in range(count):
        total_fetched = rng.randint(20, 120)
        dedup_count = rng.randint(0, 10)
        error_count = rng.randint(0, 5)
        staged_count = max(total_fetched - dedup_count - error_count, 0)
        batch_id = f"batch-{index:04d}-{rng.randint(1000, 9999)}"
        region_id = f"region-{rng.randint(1, 8):02d}"
        correlation_id = f"corr-{seed}-{index:04d}-{rng.randint(10000, 99999)}"

        yield EventEnvelope(
            correlation_id=correlation_id,
            agent_id="ingestion-agent",
            payload=ingest_batch_payload(
                batch_id=batch_id,
                source="synthetic-harness-fixture",
                region_id=region_id,
                total_fetched=total_fetched,
                staged_count=staged_count,
                dedup_count=dedup_count,
                error_count=error_count,
            ),
        )


def generate_ingest_batches(
    *, count: int = 1000, seed: int = 42
) -> Iterable[EventEnvelope]:
    """Shared stream source for all Week 3 transport parity tests."""
    if _harness_generator is not None:
        yield from _harness_generator(count=count, seed=seed)
        return

    yield from fixture_synthetic_ingest_batches(count=count, seed=seed)
