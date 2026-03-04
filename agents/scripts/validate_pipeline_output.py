"""
Validate Task 2.4 pipeline_run.json:
- 80 entries
- Each entry has 6 envelope fields
- Each correlation_id group has exactly 8 events
- Print 3 sample correlation_id traces
"""
from __future__ import annotations

import json
from pathlib import Path

REQUIRED_KEYS = {"event_id", "correlation_id", "agent_id", "timestamp", "schema_version", "payload"}
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "output" / "pipeline_run.json"


def main() -> None:
    with open(OUTPUT_PATH, encoding="utf-8") as f:
        entries = json.load(f)

    assert len(entries) == 80, f"Expected 80 entries, got {len(entries)}"

    for i, entry in enumerate(entries):
        keys = set(entry.keys())
        assert keys == REQUIRED_KEYS, f"Entry {i} missing keys: {REQUIRED_KEYS - keys!r} or extra: {keys - REQUIRED_KEYS!r}"

    by_correlation: dict[str, list[dict]] = {}
    for entry in entries:
        cid = entry["correlation_id"]
        by_correlation.setdefault(cid, []).append(entry)

    for cid, group in by_correlation.items():
        assert len(group) == 8, f"correlation_id {cid!r} has {len(group)} events, expected 8"

    # Preserve order within each trace (entries are in pipeline order)
    sample_cids = list(by_correlation.keys())[:3]
    print("Sample correlation_id traces (agent_id order):")
    for cid in sample_cids:
        trace = [e["agent_id"] for e in by_correlation[cid]]
        print(f"  {cid}: {trace}")

    print("All checks passed.")


if __name__ == "__main__":
    main()
