"""Generate EXP-004 transport comparison HTML report with embedded graphs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from agents.common.message_bus.candidate_factories import build_transport_candidates
from agents.common.message_bus.comparison import (
    ComparisonScenario,
    TransportComparisonResult,
    compare_transport_candidates,
    results_to_rows,
)
from agents.common.message_bus.run_comparison import _parse_bootstrap_servers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run transport comparison and generate HTML report with graphs."
    )
    parser.add_argument("--count", type=int, default=1000, help="Number of harness events.")
    parser.add_argument("--seed", type=int, default=42, help="Harness seed.")
    parser.add_argument("--crash-at", type=int, default=500, help="Crash index for replay.")
    parser.add_argument(
        "--skip-replay",
        action="store_true",
        help="Disable crash/replay check.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("agents/docs/exp004_transport_report.html"),
        help="Output HTML path.",
    )
    parser.add_argument("--redis-url", default=None, help="Live Redis URL (optional).")
    parser.add_argument("--kafka-bootstrap-servers", default=None, help="Live Kafka servers (optional).")
    return parser


def run_comparison(
    event_count: int = 1000,
    seed: int = 42,
    crash_at: int = 500,
    include_replay: bool = True,
    redis_url: str | None = None,
    kafka_bootstrap_servers: str | None = None,
) -> tuple[Sequence[TransportComparisonResult], ComparisonScenario]:
    scenario = ComparisonScenario(
        event_count=event_count,
        seed=seed,
        crash_at=crash_at,
        include_crash_replay=include_replay,
    )
    kafka_servers = _parse_bootstrap_servers(kafka_bootstrap_servers)
    candidates = build_transport_candidates(
        redis_url=redis_url,
        kafka_bootstrap_servers=kafka_servers,
    )
    results = compare_transport_candidates(candidates, scenario=scenario)
    return results, scenario


def build_html_report(
    results: Sequence[TransportComparisonResult],
    scenario: ComparisonScenario,
) -> str:
    rows = results_to_rows(results)
    labels = [f"{r['transport']} ({r['backend']})" for r in rows]

    # Throughput: publish vs e2e
    throughput_publish = [r["throughput_publish_events_per_sec"] for r in rows]
    throughput_e2e = [r["throughput_e2e_events_per_sec"] for r in rows]

    # Latency (use 0 when null for chart)
    latency_p50 = [r["latency_p50_ms"] if r["latency_p50_ms"] is not None else 0 for r in rows]
    latency_p95 = [r["latency_p95_ms"] if r["latency_p95_ms"] is not None else 0 for r in rows]
    latency_p99 = [r["latency_p99_ms"] if r["latency_p99_ms"] is not None else 0 for r in rows]

    # Replay / correctness
    replay_pct = [
        r["replay_completeness_pct"] if r["replay_completeness_pct"] is not None else None
        for r in rows
    ]
    correctness = [r["correctness_passed"] for r in rows]

    data_js = json.dumps({
        "labels": labels,
        "throughput_publish": throughput_publish,
        "throughput_e2e": throughput_e2e,
        "latency_p50": latency_p50,
        "latency_p95": latency_p95,
        "latency_p99": latency_p99,
        "replay_pct": replay_pct,
        "correctness": correctness,
        "rows": rows,
        "scenario": {
            "name": scenario.name,
            "event_count": scenario.event_count,
            "seed": scenario.seed,
            "replay_enabled": scenario.include_crash_replay,
        },
    })

    return _HTML_TEMPLATE.replace("__DATA__", data_js)


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EXP-004 Transport Comparison Report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f1419;
      --surface: #1a2332;
      --border: #2d3a4f;
      --text: #e6edf3;
      --muted: #8b949e;
      --accent: #58a6ff;
      --success: #3fb950;
      --warning: #d29922;
      --chart1: #58a6ff;
      --chart2: #3fb950;
      --chart3: #bc8cff;
    }
    * { box-sizing: border-box; }
    body {
      font-family: 'DM Sans', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 2rem;
      line-height: 1.5;
    }
    .container { max-width: 1100px; margin: 0 auto; }
    h1 {
      font-size: 1.75rem;
      font-weight: 700;
      margin: 0 0 0.5rem;
      letter-spacing: -0.02em;
    }
    .subtitle {
      color: var(--muted);
      font-size: 0.95rem;
      margin-bottom: 2rem;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 2rem;
      padding: 1rem 1.25rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 0.9rem;
    }
    .meta span { color: var(--muted); }
    .meta strong { color: var(--text); font-family: 'JetBrains Mono', monospace; }
    section {
      margin-bottom: 2.5rem;
    }
    section h2 {
      font-size: 1.15rem;
      font-weight: 600;
      margin: 0 0 1rem;
      color: var(--text);
    }
    .chart-wrap {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      margin-bottom: 1.5rem;
      height: 320px;
    }
    .chart-wrap.wide { height: 360px; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }
    th, td {
      padding: 0.6rem 0.9rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    th {
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      font-size: 0.75rem;
    }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(88, 166, 255, 0.06); }
    .mono { font-family: 'JetBrains Mono', monospace; }
    .badge {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 500;
    }
    .badge.ok { background: rgba(63, 185, 80, 0.2); color: var(--success); }
    .badge.na { background: rgba(139, 148, 158, 0.2); color: var(--muted); }
    .conclusion {
      padding: 1.25rem 1.5rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      border-left: 4px solid var(--accent);
    }
    .conclusion h2 { margin-top: 0; }
    .conclusion p { margin: 0.5rem 0 0; color: var(--muted); font-size: 0.95rem; }
    .conclusion p:first-of-type { margin-top: 0; color: var(--text); }
  </style>
</head>
<body>
  <div class="container">
    <h1>EXP-004 Transport Comparison</h1>
    <p class="subtitle">Event bus candidate benchmark — publish throughput, end-to-end throughput, latency (p50/p95/p99), and crash/replay completeness.</p>

    <div class="meta" id="meta"></div>

    <section>
      <h2>Throughput (events/sec)</h2>
      <div class="chart-wrap wide">
        <canvas id="chartThroughput"></canvas>
      </div>
      <p class="subtitle" style="margin-top: 0.5rem;">Publish: rate at which events are published. End-to-end: rate including handler execution and drain.</p>
    </section>

    <section>
      <h2>Publish-to-handler latency (ms)</h2>
      <div class="chart-wrap">
        <canvas id="chartLatency"></canvas>
      </div>
      <p class="subtitle" style="margin-top: 0.5rem;">p50, p95, p99 — in-process is sync so latency is near zero; Redis/Kafka include serialization and drain.</p>
    </section>

    <section>
      <h2>Correctness &amp; replay</h2>
      <div class="chart-wrap">
        <canvas id="chartReplay"></canvas>
      </div>
      <p class="subtitle" style="margin-top: 0.5rem;">Replay completeness % (after simulated crash). In-process has no replay (N/A).</p>
    </section>

    <section>
      <h2>Full results</h2>
      <div style="overflow-x: auto;">
        <table id="tableResults"></table>
      </div>
    </section>

    <section>
      <div class="conclusion">
        <h2>Conclusion</h2>
        <p><strong>Phase 1:</strong> Use <strong>in-process</strong> event bus — highest throughput, lowest latency, no extra infrastructure. Matches architecture (in-process pub/sub for Phase 1).</p>
        <p><strong>Phase 2:</strong> Re-run this report with live Redis or Kafka (e.g. <code>--redis-url</code> / <code>--kafka-bootstrap-servers</code>) when durability, replay, or multi-process consumption is required.</p>
      </div>
    </section>
  </div>

  <script>
    const data = __DATA__;

    // Meta
    const s = data.scenario;
    document.getElementById('meta').innerHTML = [
      '<span>Scenario</span> <strong>' + s.name + '</strong>',
      '<span>Events</span> <strong>' + s.event_count + '</strong>',
      '<span>Seed</span> <strong>' + s.seed + '</strong>',
      '<span>Replay</span> <strong>' + (s.replay_enabled ? 'enabled' : 'disabled') + '</strong>'
    ].join('');

    const fontFamily = "'JetBrains Mono', monospace";
    const gridColor = 'rgba(45, 58, 79, 0.8)';
    const labelColor = '#8b949e';

    // Throughput (grouped bar)
    new Chart(document.getElementById('chartThroughput'), {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [
          { label: 'Publish throughput (events/s)', data: data.throughput_publish, backgroundColor: 'rgba(88, 166, 255, 0.7)', borderColor: '#58a6ff', borderWidth: 1 },
          { label: 'End-to-end throughput (events/s)', data: data.throughput_e2e, backgroundColor: 'rgba(63, 185, 80, 0.7)', borderColor: '#3fb950', borderWidth: 1 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: labelColor } } },
        scales: {
          x: { grid: { color: gridColor }, ticks: { color: labelColor, font: { family: fontFamily, size: 11 } } },
          y: { grid: { color: gridColor }, ticks: { color: labelColor, font: { family: fontFamily } } }
        }
      }
    });

    // Latency (grouped bar)
    new Chart(document.getElementById('chartLatency'), {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [
          { label: 'p50 (ms)', data: data.latency_p50, backgroundColor: 'rgba(88, 166, 255, 0.6)', borderColor: '#58a6ff', borderWidth: 1 },
          { label: 'p95 (ms)', data: data.latency_p95, backgroundColor: 'rgba(63, 185, 80, 0.6)', borderColor: '#3fb950', borderWidth: 1 },
          { label: 'p99 (ms)', data: data.latency_p99, backgroundColor: 'rgba(188, 140, 255, 0.6)', borderColor: '#bc8cff', borderWidth: 1 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: labelColor } } },
        scales: {
          x: { grid: { color: gridColor }, ticks: { color: labelColor, font: { family: fontFamily, size: 11 } } },
          y: { grid: { color: gridColor }, ticks: { color: labelColor, font: { family: fontFamily } } }
        }
      }
    });

    // Replay completeness (%); correctness as secondary
    const replayData = data.replay_pct.map(function (v) { return v != null ? v : 0; });
    new Chart(document.getElementById('chartReplay'), {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [
          { label: 'Replay completeness (%)', data: replayData, backgroundColor: 'rgba(188, 140, 255, 0.7)', borderColor: '#bc8cff', borderWidth: 1 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: { legend: { labels: { color: labelColor } } },
        scales: {
          x: { min: 0, max: 100, grid: { color: gridColor }, ticks: { color: labelColor, font: { family: fontFamily } } },
          y: { grid: { color: gridColor }, ticks: { color: labelColor, font: { family: fontFamily, size: 11 } } }
        }
      }
    });

    // Table
    const rows = data.rows;
    if (rows.length) {
      const keys = Object.keys(rows[0]);
      let thead = '<thead><tr>' + keys.map(function (k) { return '<th>' + k + '</th>'; }).join('') + '</tr></thead>';
      let tbody = '<tbody>';
      rows.forEach(function (r) {
        tbody += '<tr>';
        keys.forEach(function (k) {
          let v = r[k];
          if (v === null || v === undefined) v = 'N/A';
          else if (typeof v === 'number' && (v * 100) % 1 !== 0) v = v.toFixed(2);
          else if (typeof v === 'boolean') v = v ? 'true' : 'false';
          tbody += '<td class="mono">' + v + '</td>';
        });
        tbody += '</tr>';
      });
      tbody += '</tbody>';
      document.getElementById('tableResults').innerHTML = thead + tbody;
    }
  </script>
</body>
</html>
"""


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    crash_at = args.crash_at
    if not args.skip_replay and crash_at > args.count:
        crash_at = max(1, args.count // 2)

    results, scenario = run_comparison(
        event_count=args.count,
        seed=args.seed,
        crash_at=crash_at,
        include_replay=not args.skip_replay,
        redis_url=args.redis_url,
        kafka_bootstrap_servers=args.kafka_bootstrap_servers,
    )
    html = build_html_report(results, scenario)
    out = args.output
    if not out.is_absolute():
        # Assume run from repo root
        repo = Path(__file__).resolve().parent.parent.parent.parent
        out = repo / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Report written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
