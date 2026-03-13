"""CLI entry point for EXP-004 transport comparisons."""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from agents.common.message_bus.candidate_factories import build_transport_candidates
from agents.common.message_bus.comparison import (
    ComparisonScenario,
    TransportComparisonResult,
    compare_transport_candidates,
    format_results_markdown_table,
    results_to_rows,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the transport comparison command."""
    parser = argparse.ArgumentParser(
        description="Run the shared EXP-004 transport comparison across all three buses."
    )
    parser.add_argument("--count", type=int, default=1000, help="Number of input harness events.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic harness seed.")
    parser.add_argument(
        "--latency-sample-size",
        type=int,
        default=None,
        help="Optional cap on latency samples collected per run.",
    )
    parser.add_argument("--crash-at", type=int, default=500, help="Crash index for replay checks.")
    parser.add_argument(
        "--skip-replay",
        action="store_true",
        help="Disable the crash/replay completeness check.",
    )
    parser.add_argument(
        "--drain-batch-size",
        type=int,
        default=256,
        help="Max events consumed per drain iteration.",
    )
    parser.add_argument(
        "--drain-iteration-limit",
        type=int,
        default=10_000,
        help="Safety cap on drain loop iterations.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "csv", "json"),
        default="markdown",
        help="Output format for the comparison results.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to also write the rendered output.",
    )
    parser.add_argument(
        "--redis-url",
        default=None,
        help="Use a live Redis backend instead of the fake Redis Streams client.",
    )
    parser.add_argument(
        "--redis-stream-name",
        default="exp004:events",
        help="Redis stream name for live or fake runs.",
    )
    parser.add_argument(
        "--redis-group-name",
        default="exp004-group",
        help="Redis consumer group name for live or fake runs.",
    )
    parser.add_argument(
        "--redis-consumer-name",
        default="exp004-consumer",
        help="Redis consumer name for live or fake runs.",
    )
    parser.add_argument(
        "--kafka-bootstrap-servers",
        default=None,
        help="Comma-separated bootstrap servers to use a live Kafka backend.",
    )
    parser.add_argument(
        "--kafka-topic",
        default="exp004.events",
        help="Kafka topic for live or fake runs.",
    )
    parser.add_argument(
        "--kafka-group-id",
        default="exp004-group",
        help="Kafka consumer group id for live runs.",
    )
    parser.add_argument(
        "--kafka-client-id",
        default="exp004-consumer",
        help="Kafka client id for live runs.",
    )
    parser.add_argument(
        "--kafka-auto-offset-reset",
        choices=("earliest", "latest"),
        default="earliest",
        help="Kafka auto offset reset policy for live runs.",
    )
    return parser


def main(argv: Sequence[str] | None = None, *, out: TextIO | None = None) -> int:
    """Run the transport comparison command."""
    parser = build_parser()
    args = parser.parse_args(argv)
    output = out or io.StringIO()
    crash_at = min(max(args.crash_at, 1), args.count)

    scenario = ComparisonScenario(
        event_count=args.count,
        seed=args.seed,
        drain_batch_size=args.drain_batch_size,
        drain_iteration_limit=args.drain_iteration_limit,
        latency_sample_size=args.latency_sample_size,
        include_crash_replay=not args.skip_replay,
        crash_at=crash_at,
    )
    kafka_bootstrap_servers = _parse_bootstrap_servers(args.kafka_bootstrap_servers)
    candidates = build_transport_candidates(
        redis_url=args.redis_url,
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        redis_stream_name=args.redis_stream_name,
        redis_group_name=args.redis_group_name,
        redis_consumer_name=args.redis_consumer_name,
        kafka_topic=args.kafka_topic,
        kafka_group_id=args.kafka_group_id,
        kafka_client_id=args.kafka_client_id,
        kafka_auto_offset_reset=args.kafka_auto_offset_reset,
    )
    results = compare_transport_candidates(candidates, scenario=scenario)
    rendered = render_report(results, scenario=scenario, output_format=args.format)
    output.write(rendered)
    if not rendered.endswith("\n"):
        output.write("\n")

    if args.output is not None:
        args.output.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")

    if out is None:
        import sys

        sys.stdout.write(output.getvalue())

    return 0


def render_report(
    results: Sequence[TransportComparisonResult],
    *,
    scenario: ComparisonScenario,
    output_format: str = "markdown",
) -> str:
    """Render results for stdout or a file."""
    if output_format == "csv":
        return _render_csv(results)
    if output_format == "json":
        return json.dumps(results_to_rows(results), indent=2)
    if output_format != "markdown":
        raise ValueError(f"unsupported output format '{output_format}'")

    summary = _render_markdown_summary(results, scenario=scenario)
    table = format_results_markdown_table(results)
    return f"{summary}\n\n{table}"


def _render_markdown_summary(
    results: Sequence[TransportComparisonResult],
    *,
    scenario: ComparisonScenario,
) -> str:
    fastest_publish = max(results, key=lambda result: result.throughput_publish_events_per_sec)
    fastest_e2e = max(results, key=lambda result: result.throughput_e2e_events_per_sec)
    latency_candidates = [
        result for result in results if result.latency_p95_ms is not None
    ]
    lowest_p95 = min(latency_candidates, key=lambda result: result.latency_p95_ms or 0)
    replay_label = "enabled" if scenario.include_crash_replay else "disabled"
    producer_crash_lines = [
        result
        for result in results
        if result.producer_crash_loss_count is not None
        and result.producer_resume_recovered_count is not None
        and result.producer_resume_complete is not None
    ]
    producer_summary = None
    if producer_crash_lines:
        max_loss = max(
            result.producer_crash_loss_count or 0 for result in producer_crash_lines
        )
        min_recovered = min(
            result.producer_resume_recovered_count or 0
            for result in producer_crash_lines
        )
        all_recovered = all(
            result.producer_resume_complete is True
            for result in producer_crash_lines
        )
        producer_summary = (
            f"Producer crash at `{scenario.crash_at}`: immediate loss `{max_loss}` "
            f"events; resumed recovery `{min_recovered}` events; "
            f"complete after resume: `{all_recovered}`"
        )

    lines = [
        "# EXP-004 Transport Comparison",
        "",
        (
            f"Scenario: `{scenario.name}` | Input events: `{scenario.event_count}` | "
            f"Seed: `{scenario.seed}` | Replay: `{replay_label}`"
        ),
        (
            f"Best publish throughput: `{fastest_publish.transport}` / `{fastest_publish.backend}` "
            f"at `{fastest_publish.throughput_publish_events_per_sec:.2f}` events/sec"
        ),
        (
            f"Best end-to-end throughput: `{fastest_e2e.transport}` / `{fastest_e2e.backend}` "
            f"at `{fastest_e2e.throughput_e2e_events_per_sec:.2f}` events/sec"
        ),
        (
            f"Lowest p95 latency: `{lowest_p95.transport}` / `{lowest_p95.backend}` "
            f"at `{(lowest_p95.latency_p95_ms or 0):.2f}` ms"
        ),
    ]
    if producer_summary is not None:
        lines.append(producer_summary)

    return "\n".join(lines)


def _render_csv(results: Sequence[TransportComparisonResult]) -> str:
    rows = results_to_rows(results)
    if not rows:
        return ""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().rstrip("\n")


def _parse_bootstrap_servers(raw: str | None) -> str | list[str] | None:
    if raw is None:
        return None
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return parts


if __name__ == "__main__":
    raise SystemExit(main())
