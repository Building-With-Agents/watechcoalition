"""Tests for the transport comparison CLI."""

from __future__ import annotations

import io

from agents.common.message_bus.comparison import (
    ComparisonScenario,
    TransportComparisonResult,
)
from agents.common.message_bus.run_comparison import main, render_report


def test_cli_main_renders_markdown_report_to_stdout_buffer() -> None:
    buffer = io.StringIO()
    exit_code = main(
        [
            "--count",
            "10",
            "--skip-replay",
            "--format",
            "markdown",
        ],
        out=buffer,
    )

    rendered = buffer.getvalue()
    assert exit_code == 0
    assert "# EXP-004 Transport Comparison" in rendered
    assert "in_process" in rendered
    assert "redis_streams" in rendered
    assert "kafka" in rendered
    assert "Producer crash at `10`" in rendered


def test_render_report_csv_outputs_header_and_values() -> None:
    report = render_report(
        [
            TransportComparisonResult(
                scenario_name="scenario",
                transport="in_process",
                backend="in_memory",
                input_events=10,
                throughput_publish_events_per_sec=100.0,
                throughput_e2e_events_per_sec=90.0,
                latency_p50_ms=1.0,
                latency_p95_ms=2.0,
                latency_p99_ms=3.0,
                latency_sample_count=10,
                crash_replay_complete=None,
                replay_completeness_pct=None,
                producer_crash_published_before_crash=10,
                producer_crash_delivered_before_crash=10,
                producer_crash_loss_count=0,
                producer_resume_recovered_count=0,
                producer_resume_final_loss_count=0,
                producer_resume_complete=True,
                published_events=20,
                delivered_events=20,
                handler_failures=0,
                queue_depth=None,
                in_flight=None,
                drain_iterations=0,
                correctness_passed=True,
            )
        ],
        scenario=ComparisonScenario(event_count=10, include_crash_replay=False),
        output_format="csv",
    )

    assert "transport,backend,throughput_publish_events_per_sec" in report
    assert "in_process,in_memory,100.0,90.0,1.0,2.0,3.0" in report
