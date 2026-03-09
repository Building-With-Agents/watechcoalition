"""
View and check the EXP-004 test harness output.

Run from repo root:
  python -m agents.common.events.view_harness
  python -m agents.common.events.view_harness --count 10 --seed 42
  python -m agents.common.events.view_harness --count 1000   # full harness
  python -m agents.common.events.view_harness --count 1 --json   # first event as JSON
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from agents.common.event_envelope import EventEnvelope
from agents.common.events.ingest_batch_harness import (
    assert_valid_ingest_batch_envelope,
    generate_synthetic_ingest_batches,
)


def _envelope_to_dict(event: EventEnvelope) -> dict:
    e = event
    return {
        "event_id": e.event_id,
        "correlation_id": e.correlation_id,
        "agent_id": e.agent_id,
        "timestamp": (
            e.timestamp.isoformat()
            if isinstance(e.timestamp, datetime)
            else str(e.timestamp)
        ),
        "schema_version": e.schema_version,
        "payload": e.payload,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="View and validate harness-generated IngestBatch events."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of events (default 5; use 1000 for full harness)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed for deterministic generation (default 42)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print first event as JSON only",
    )
    args = parser.parse_args()

    events = list(generate_synthetic_ingest_batches(count=args.count, seed=args.seed))

    if args.json:
        if not events:
            print("{}")
            return
        print(json.dumps(_envelope_to_dict(events[0]), indent=2))
        return

    print("=" * 60)
    print("EXP-004 Test Harness — View & Check")
    print("=" * 60)
    print(f"Count: {args.count}  |  Seed: {args.seed}\n")

    try:
        for event in events:
            assert_valid_ingest_batch_envelope(event)
        print(f"Validation: all {len(events)} event(s) valid.")
    except ValueError as err:
        print(f"Validation FAIL: {err}")
    print()

    if events:
        first = events[0]
        print("--- First event (envelope + payload) ---")
        print(f"  event_id:        {first.event_id}")
        print(f"  correlation_id:  {first.correlation_id}")
        print(f"  agent_id:        {first.agent_id}")
        print(f"  timestamp:       {first.timestamp}")
        print(f"  schema_version:  {first.schema_version}")
        print("  payload:")
        for k, v in first.payload.items():
            print(f"    {k}: {v!r}")
        print()

    if len(events) > 1:
        last = events[-1]
        print("--- Last event (summary) ---")
        print(f"  event_id:   {last.event_id}")
        print(f"  batch_id:   {last.payload.get('batch_id')}")
        print(f"  payload:   {last.payload}\n")

    ids = [e.event_id for e in events]
    print(
        f"Uniqueness: {'OK (all event_ids unique)' if len(set(ids)) == len(ids) else 'FAIL'}"
    )
    run2 = next(generate_synthetic_ingest_batches(count=args.count, seed=args.seed))
    det_ok = (
        run2.event_id == events[0].event_id and run2.payload == events[0].payload
    )
    print(
        f"Determinism: {'OK (same seed => same first event)' if det_ok else 'FAIL'}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
