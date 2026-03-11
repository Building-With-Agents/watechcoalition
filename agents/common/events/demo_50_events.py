"""
Demo: generate 50 success events, then 50 events that include both error types.

Shows what "happy path" vs "stream with failures" looks like. Run from repo root:

  python -m agents.common.events.demo_50_events
"""
# ruff: noqa: T201

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope
from agents.common.events.ingest_batch_harness import (
    assert_valid_ingest_batch_envelope,
    generate_synthetic_ingest_batches,
)
from agents.common.events.synthetic_events import (
    generate_synthetic_normalization_failed,
    generate_synthetic_source_failures,
)


def _payload_type(e: EventEnvelope) -> str:
    return e.payload.get("event_type", "?")


def main() -> None:
    print("=" * 70)
    print("EXP-004 Demo: 50 success events, then 50 events with both error types")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Part 1: 50 "success" events (IngestBatch only — happy path)
    # -------------------------------------------------------------------------
    print("\n--- Part 1: 50 SUCCESS events (IngestBatch only) ---\n")
    success_events = list(
        generate_synthetic_ingest_batches(count=50, seed=100, typed=False)
    )
    for e in success_events:
        assert_valid_ingest_batch_envelope(e)

    print(f"  Generated: {len(success_events)} events")
    print(f"  event_type:  {_payload_type(success_events[0])} (all same)")
    print(f"  correlation_id: {success_events[0].correlation_id}")
    print(f"  agent_id:    {success_events[0].agent_id}")
    print("\n  First event payload (success):")
    for k, v in success_events[0].payload.items():
        print(f"    {k}: {v}")
    print("\n  Last event batch_id:", success_events[-1].payload.get("batch_id"))

    # -------------------------------------------------------------------------
    # Part 2: 50 events that include BOTH error types (success + SourceFailure + NormalizationFailed)
    # -------------------------------------------------------------------------
    print("\n--- Part 2: 50 events WITH BOTH ERROR TYPES ---\n")
    # Mix: 20 IngestBatch, 15 SourceFailure, 15 NormalizationFailed = 50
    ingest = list(generate_synthetic_ingest_batches(count=20, seed=200, typed=False))
    source_fail = list(
        generate_synthetic_source_failures(count=15, seed=200, typed=False)
    )
    norm_fail = list(
        generate_synthetic_normalization_failed(count=15, seed=200, typed=False)
    )
    mixed_events: list[EventEnvelope] = [*ingest, *source_fail, *norm_fail]

    print(f"  Total: {len(mixed_events)} events")
    print(f"    - IngestBatch (success):          {len(ingest)}")
    print(f"    - SourceFailure (ingestion err):  {len(source_fail)}")
    print(f"    - NormalizationFailed (norm err): {len(norm_fail)}")

    print("\n  Sample IngestBatch payload (success):")
    for k, v in ingest[0].payload.items():
        print(f"    {k}: {v}")

    print("\n  Sample SourceFailure payload (error_type, severity, error_reason):")
    sf = source_fail[0].payload
    print(f"    event_type:   {sf.get('event_type')}")
    print(f"    source:       {sf.get('source')}")
    print(f"    error:        {sf.get('error')}")
    print(f"    error_type:   {sf.get('error_type')}")
    print(f"    severity:     {sf.get('severity')}")
    print(f"    error_reason: {sf.get('error_reason')}")

    print("\n  Sample NormalizationFailed payload:")
    nf = norm_fail[0].payload
    print(f"    event_type:   {nf.get('event_type')}")
    print(f"    batch_id:     {nf.get('batch_id')}")
    print(f"    error:        {nf.get('error')}")
    print(f"    error_type:   {nf.get('error_type')}")
    print(f"    severity:     {nf.get('severity')}")
    print(f"    error_reason: {nf.get('error_reason')}")

    print("\n" + "=" * 70)
    print("Summary: Part 1 = 50 success-only events. Part 2 = 50 mixed (success + both error types).")
    print("=" * 70)


if __name__ == "__main__":
    main()
