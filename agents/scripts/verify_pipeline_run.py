"""
Task 2.4 verification: validate pipeline_run.json.

Checks: file exists, 80 events, input_record_count 10, every event has all six
envelope fields, 10 unique correlation_ids each appearing 8 times.

Run from repo root:
  python -m agents.scripts.verify_pipeline_run
  python -m agents.scripts.verify_pipeline_run agents/data/output/pipeline_run.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_FIELDS = {"event_id", "correlation_id", "agent_id", "timestamp", "schema_version", "payload"}
EXPECTED_RECORDS = 10
EXPECTED_AGENTS_PER_RECORD = 8
EXPECTED_EVENTS = EXPECTED_RECORDS * EXPECTED_AGENTS_PER_RECORD  # 80


def main() -> int:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        # Resolve path from this file: agents/scripts -> agents/
        _agents = Path(__file__).resolve().parents[1]
        path = _agents / "data" / "output" / "pipeline_run.json"

    if not path.exists():
        print(f"FAIL: File not found: {path}")
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"FAIL: Could not read JSON: {e}")
        return 1

    events = data.get("events")
    if not isinstance(events, list):
        print("FAIL: 'events' is missing or not a list")
        return 1

    ok = True
    input_count = data.get("input_record_count")
    if input_count != EXPECTED_RECORDS:
        print(f"FAIL: input_record_count={input_count}, expected {EXPECTED_RECORDS}")
        ok = False
    else:
        print(f"OK: input_record_count={EXPECTED_RECORDS}")

    if len(events) != EXPECTED_EVENTS:
        print(f"FAIL: events length={len(events)}, expected {EXPECTED_EVENTS}")
        ok = False
    else:
        print(f"OK: events length={EXPECTED_EVENTS}")

    missing = []
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            missing.append((i, "not a dict"))
            continue
        for f in REQUIRED_FIELDS:
            if f not in ev:
                missing.append((i, f"missing field '{f}'"))
    if missing:
        print(f"FAIL: envelope field issues (first 5): {missing[:5]}")
        return 1
    print("OK: every event has all six envelope fields")

    from collections import Counter
    cid_counts = Counter(ev.get("correlation_id") for ev in events)
    unique_cids = len(cid_counts)
    if unique_cids != EXPECTED_RECORDS:
        print(f"FAIL: unique correlation_ids={unique_cids}, expected {EXPECTED_RECORDS}")
        ok = False
    else:
        print(f"OK: {EXPECTED_RECORDS} unique correlation_ids")
    bad = [cid for cid, count in cid_counts.items() if count != EXPECTED_AGENTS_PER_RECORD]
    if bad:
        print(f"FAIL: correlation_ids with count != {EXPECTED_AGENTS_PER_RECORD}: {bad[:3]}...")
        ok = False
    else:
        print(f"OK: each correlation_id appears exactly {EXPECTED_AGENTS_PER_RECORD} times")

    event_ids = [ev.get("event_id") for ev in events]
    if len(event_ids) != len(set(event_ids)):
        print("FAIL: duplicate event_id values")
        ok = False
    else:
        print("OK: all event_id values unique within run")

    if ok:
        print("Verification passed.")
        return 0
    print("Verification failed (see FAIL lines above).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
