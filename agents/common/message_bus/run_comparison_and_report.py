"""Run EXP-004 transport comparison (1000, seed 42), write CSV, then print five-metric summary."""

from __future__ import annotations

import csv
import os
from pathlib import Path

from agents.common.message_bus.candidate_factories import build_transport_candidates
from agents.common.message_bus.comparison import (
    ComparisonScenario,
    compare_transport_candidates,
    results_to_rows,
)
from agents.common.message_bus.comparison_charts import generate_charts


def _default_csv_path() -> Path:
    return Path(os.getenv("EXP004_COMPARISON_CSV", "agents/data/output/exp004_comparison.csv"))


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    _ensure_parent_dir(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _format_val(value: object) -> str:
    if value is None or value == "":
        return "N/A"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _print_report(rows: list[dict[str, str]]) -> None:
    if not rows:
        print("No results to report.")
        return

    print("\n" + "=" * 60)
    print("EXP-004 Comparison Summary (from CSV)")
    print("=" * 60)

    print("\n--- Throughput (events consumed per second) ---")
    for row in rows:
        transport = row.get("transport", "?")
        backend = row.get("backend", "?")
        e2e = row.get("throughput_e2e_events_per_sec", "")
        print(f"  {transport} / {backend}: {_format_val(e2e)} events/sec")

    print("\n--- Latency (publish to consumed) ---")
    print("  Latency = publish to consumed (handler finished).")
    for row in rows:
        transport = row.get("transport", "?")
        backend = row.get("backend", "?")
        p50 = row.get("latency_p50_ms", "")
        p95 = row.get("latency_p95_ms", "")
        p99 = row.get("latency_p99_ms", "")
        print(f"  {transport} / {backend}: p50={_format_val(p50)} ms, p95={_format_val(p95)} ms, p99={_format_val(p99)} ms")

    print("\n--- Max in-flight ---")
    print("  Peak events sent but not yet acknowledged (or N/A).")
    for row in rows:
        transport = row.get("transport", "?")
        backend = row.get("backend", "?")
        max_if = row.get("max_in_flight", row.get("in_flight", ""))
        print(f"  {transport} / {backend}: {_format_val(max_if)}")

    print("\n--- Replay ---")
    for row in rows:
        transport = row.get("transport", "?")
        backend = row.get("backend", "?")
        replay_count = row.get("replay_count", "")
        replay_pct = row.get("replay_completeness_pct", "")
        complete = row.get("crash_replay_complete", "")
        print(f"  {transport} / {backend}: replay_count={_format_val(replay_count)}, replay_completeness_pct={_format_val(replay_pct)}, crash_replay_complete={_format_val(complete)}")

    print("\n--- Correlation ID propagation ---")
    corr_key = "correlation_id_propagation_passed"
    if rows and corr_key not in rows[0]:
        corr_key = "correctness_passed"
    for row in rows:
        transport = row.get("transport", "?")
        backend = row.get("backend", "?")
        passed = row.get(corr_key, "")
        print(f"  {transport} / {backend}: {_format_val(passed)}")

    if rows and "producer_crash_delivered" in rows[0]:
        print("\n--- Producer crash (at 500) ---")
        for row in rows:
            transport = row.get("transport", "?")
            backend = row.get("backend", "?")
            delivered = row.get("producer_crash_delivered", "")
            lost = row.get("producer_crash_events_lost", "")
            print(f"  {transport} / {backend}: delivered={_format_val(delivered)}, events_lost={_format_val(lost)}")

    if rows and "events_lost_consumer_crash" in rows[0]:
        print("\n--- Consumer crash event loss ---")
        for row in rows:
            transport = row.get("transport", "?")
            backend = row.get("backend", "?")
            lost = row.get("events_lost_consumer_crash", "")
            print(f"  {transport} / {backend}: events_lost={_format_val(lost)}")

    print("\n" + "=" * 60)


def main() -> int:
    scenario = ComparisonScenario(
        event_count=1000,
        seed=42,
        include_crash_replay=True,
        crash_at=500,
        producer_crash_at=500,
    )
    candidates = build_transport_candidates()
    results = compare_transport_candidates(candidates, scenario=scenario)
    rows = results_to_rows(results)

    csv_path = _default_csv_path()
    _write_csv(csv_path, rows)
    print(f"Wrote CSV to {csv_path}")

    chart_paths = generate_charts(csv_path)
    if chart_paths:
        print("Charts saved:")
        for p in chart_paths:
            print(f"  {p}")

    read_back = _read_csv(csv_path)
    _print_report(read_back)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
