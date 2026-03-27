"""
Run the full pipeline with Redis Streams as the message bus and emit metrics + HTML report.

**Phase 1 default:** use ``agents/pipeline_runner.py`` (sequential agents, no Redis).
This script is an optional **Phase 2 / SA #14 prototype** for external-bus validation;
it is not required for normal development or CI.

Runs with a limit of 10 jobs (ingestion + skills extraction) for faster runs. To change:
- Edit _trigger_payload() and set "limit" (and/or "region_config.limit") for ingestion.
- Set env SKILLS_EXTRACTION_MAX_JOBS (default 10) to cap skills extraction work items.

Usage (from repo root, venv activated):
  python agents/pipeline_runner.py
  python -m agents.scripts.run_full_pipeline_redis --redis-url redis://localhost:6379/0
  python -m agents.scripts.run_full_pipeline_redis  # uses REDIS_URL from env

Redis is only required for this script. Output: agents/eval/full_pipeline_redis_metrics.json and .html.
"""
# ruff: noqa: T201

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from agents.analytics.agent import AnalyticsAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.llm_adapter import register_alert_bus as register_llm_alert_bus
from agents.common.message_bus.redis_streams import (
    RedisDependencyError,
    RedisStreamsError,
    RedisStreamsEventBus,
)
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.agent import register_alert_bus as register_enrichment_alert_bus
from agents.ingestion.agent import IngestionAgent
from agents.normalization.agent import NormalizationAgent
from agents.orchestration.agent import OrchestrationAgent
from agents.skills_extraction.agent import SkillsExtractionAgent
from agents.visualization.agent import VisualizationAgent

STREAM_PREFIX = "pipeline"
STAGES = [
    ("ingestion", IngestionAgent(), "PipelineTrigger", "normalization"),
    ("normalization", NormalizationAgent(), "IngestBatch", "skills"),
    ("skills", SkillsExtractionAgent(), "NormalizationComplete", "enrichment"),
    ("enrichment", EnrichmentAgent(), "SkillsExtracted", "analytics"),
    ("analytics", AnalyticsAgent(), "RecordEnriched", "visualization"),
    ("visualization", VisualizationAgent(), "AnalyticsRefreshed", "orchestration"),
    ("orchestration", OrchestrationAgent(), "RenderComplete", None),
]


def _trigger_payload() -> dict:
    """Trigger payload for one pipeline run. Uses limit=10 for faster runs; change here or via region_config."""
    return {
        "event_type": "PipelineTrigger",
        "limit": 10,
        "region_config": {
            "region_id": "borderplex-default",
            "display_name": "Borderplex Region",
            "query_location": "El Paso Texas",
            "radius_miles": 50,
            "states": ["TX", "NM"],
            "countries": ["US"],
            "sources": ["jsearch", "crawl4ai"],
            "role_categories": ["Software Engineering"],
            "keywords": ["software engineer"],
            "limit": 10,
        },
    }


def _run(
    redis_url: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Run full pipeline over Redis, collect metrics, return run result."""
    correlation_id = f"redis-pipe-{uuid.uuid4().hex[:8]}"
    metrics: list[dict[str, Any]] = []
    run_start = time.perf_counter()

    try:
        client = __import__("redis").Redis.from_url(redis_url)
        client.ping()
    except Exception as e:
        return {
            "success": False,
            "error": f"Redis connection failed: {e}",
            "correlation_id": correlation_id,
            "stages": [],
            "e2e_latency_ms": None,
            "run_start_iso": datetime.now(timezone.utc).isoformat(),
        }

    buses: list[RedisStreamsEventBus] = []
    bus_by_name: dict[str, RedisStreamsEventBus] = {}

    for stage_name, _agent, _sub_event, _next_stage in STAGES:
        stream_name = f"{STREAM_PREFIX}:{stage_name}"
        group_name = f"{STREAM_PREFIX}:{stage_name}-group"
        bus = RedisStreamsEventBus.from_url(
            redis_url,
            stream_name=stream_name,
            group_name=group_name,
            consumer_name=f"{STREAM_PREFIX}-consumer",
            group_start_id="0",
        )
        buses.append(bus)
        bus_by_name[stage_name] = bus

    orchestration_bus = bus_by_name["orchestration"]
    register_llm_alert_bus(orchestration_bus)
    register_enrichment_alert_bus(orchestration_bus)

    def make_handler(
        stage_name: str,
        agent: Any,
        next_stage: str | None,
    ) -> Any:
        def handler(event: EventEnvelope) -> None:
            stage_start = time.perf_counter()
            entry = {
                "stage": stage_name,
                "event_type_in": event.payload.get("event_type"),
                "event_type_out": None,
                "event_id_out": None,
                "start_ts": datetime.now(timezone.utc).isoformat(),
                "end_ts": None,
                "latency_ms": None,
                "success": False,
                "error": None,
                "payload_summary": None,
            }
            try:
                outbound = agent.process(event)
                stage_end = time.perf_counter()
                entry["end_ts"] = datetime.now(timezone.utc).isoformat()
                entry["latency_ms"] = round((stage_end - stage_start) * 1000, 2)
                entry["success"] = outbound is not None
                if outbound is not None:
                    entry["event_type_out"] = outbound.payload.get("event_type")
                    entry["event_id_out"] = outbound.event_id
                    entry["payload_summary"] = {
                        "event_type": outbound.payload.get("event_type"),
                        "batch_id": outbound.payload.get("batch_id"),
                        "job_ids": outbound.payload.get("job_ids"),
                    }
                metrics.append(entry)
                if outbound is not None and next_stage is not None:
                    next_bus = bus_by_name[next_stage]
                    next_bus.publish(outbound)
            except Exception as e:
                stage_end = time.perf_counter()
                entry["end_ts"] = datetime.now(timezone.utc).isoformat()
                entry["latency_ms"] = round((stage_end - stage_start) * 1000, 2)
                entry["success"] = False
                entry["error"] = str(e)
                entry["traceback"] = traceback.format_exc()
                metrics.append(entry)

        return handler

    for stage_name, agent, sub_event, next_stage in STAGES:
        bus = bus_by_name[stage_name]
        bus.subscribe(
            sub_event,
            make_handler(stage_name, agent, next_stage),
            subscriber_id=f"{stage_name}-handler",
        )

    orchestration_handler = make_handler("orchestration", OrchestrationAgent(), None)
    orchestration_bus.subscribe(
        "SkillsExtractionAlert",
        orchestration_handler,
        subscriber_id="orchestration-agent",
    )
    orchestration_bus.subscribe(
        "EnrichmentDegraded",
        orchestration_handler,
        subscriber_id="orchestration-agent",
    )

    trigger = EventEnvelope(
        correlation_id=correlation_id,
        agent_id="pipeline-runner",
        payload=_trigger_payload(),
    )
    buses[0].publish(trigger)

    for bus in buses:
        bus.consume_available(max_events=32)

    run_end = time.perf_counter()
    e2e_ms = round((run_end - run_start) * 1000, 2)
    any_failure = any(not m.get("success") for m in metrics)

    return {
        "success": not any_failure,
        "correlation_id": correlation_id,
        "stages": metrics,
        "e2e_latency_ms": e2e_ms,
        "run_start_iso": datetime.now(timezone.utc).isoformat(),
        "redis_url_used": redis_url.split("@")[-1] if "@" in redis_url else "(set)",
        "counters": {f"{STREAM_PREFIX}:{name}": bus_by_name[name].counters for name, *_ in STAGES},
    }


def _write_json(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)


def _write_html(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stages = result.get("stages", [])
    e2e = result.get("e2e_latency_ms")
    success = result.get("success", False)
    err = result.get("error")
    counters = result.get("counters") or {}

    # Timeline steps for visualization
    stage_names = [s[0] for s in STAGES]
    timeline_steps = []
    for i, name in enumerate(stage_names):
        rec = next((s for s in stages if s.get("stage") == name), None)
        if rec is None:
            timeline_steps.append(f'<div class="step skipped"><span class="step-name">{name}</span><span class="step-ms">—</span><span class="step-status">skipped</span></div>')
        else:
            status_class = "ok" if rec.get("success") else "error"
            ms = rec.get("latency_ms")
            timeline_steps.append(
                f'<div class="step {status_class}"><span class="step-name">{name}</span><span class="step-ms">{ms} ms</span><span class="step-status">{ "OK" if rec.get("success") else "ERROR" }</span></div>'
            )
        if i < len(stage_names) - 1:
            timeline_steps.append('<div class="arrow" aria-hidden="true">→</div>')
    timeline_html = "\n    ".join(timeline_steps)

    rows = []
    for s in stages:
        status = "OK" if s.get("success") else "ERROR"
        err_cell = ""
        if s.get("error"):
            err_cell = f'<pre class="err">{s["error"]}</pre>'
            if s.get("traceback"):
                err_cell += f'<pre class="tb">{s["traceback"]}</pre>'
        rows.append(
            f"""
    <tr class="{'error' if not s.get('success') else ''}">
      <td>{s.get("stage", "")}</td>
      <td>{s.get("event_type_in", "")} → {s.get("event_type_out") or "—"}</td>
      <td>{s.get("latency_ms") if s.get("latency_ms") is not None else "—"} ms</td>
      <td>{status}</td>
      <td>{err_cell}</td>
    </tr>"""
        )

    counters_rows = []
    for stream_name, c in counters.items():
        counters_rows.append(
            f"    <tr><td><code>{stream_name}</code></td><td>{c.get('published_events', '—')}</td><td>{c.get('delivered_events', '—')}</td><td>{c.get('in_flight', '—')}</td><td>{c.get('max_in_flight_seen', '—')}</td></tr>"
        )
    counters_body = "\n".join(counters_rows) if counters_rows else "    <tr><td colspan=\"5\">No counters (run failed before publish).</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Full pipeline Redis — Run report</title>
  <style>
    body {{ font-family: system-ui; max-width: 960px; margin: 1rem auto; padding: 1rem; background: #0f172a; color: #e2e8f0; }}
    h1 {{ color: #38bdf8; }}
    h2 {{ color: #94a3b8; margin-top: 1.5rem; }}
    .ok {{ color: #4ade80; }}
    .error {{ background: #7f1d1d; color: #fecaca; }}
    .err {{ font-size: 0.85rem; white-space: pre-wrap; margin: 0.25rem 0; }}
    .tb {{ font-size: 0.75rem; opacity: 0.9; }}
    table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
    th, td {{ padding: 0.5rem; text-align: left; border-bottom: 1px solid #334155; }}
    th {{ color: #94a3b8; }}
    .e2e {{ margin: 1rem 0; font-size: 1.1rem; }}
    .timeline {{ display: flex; flex-wrap: wrap; align-items: center; gap: 0.25rem; margin: 1rem 0; }}
    .step {{ padding: 0.35rem 0.6rem; border-radius: 6px; display: inline-flex; align-items: center; gap: 0.5rem; }}
    .step.ok {{ background: #14532d; color: #4ade80; }}
    .step.error {{ background: #7f1d1d; color: #fecaca; }}
    .step.skipped {{ background: #334155; color: #94a3b8; }}
    .arrow {{ color: #64748b; }}
    .step-ms {{ font-size: 0.9rem; opacity: 0.9; }}
  </style>
</head>
<body>
  <h1>Full pipeline Redis — Run report</h1>
  <p>Correlation ID: <code>{result.get("correlation_id", "")}</code></p>
  <p class="e2e">End-to-end latency: <strong>{e2e} ms</strong> | Overall: <strong class="{'ok' if success else 'error'}">{'Success' if success else 'Failure'}</strong></p>
  {f'<p class="error">Redis error: {err}</p>' if err else ''}

  <h2>Timeline (locate the failing stage)</h2>
  <div class="timeline" role="list">
{timeline_html}
  </div>

  <h2>Per-stage details</h2>
  <table>
    <thead><tr><th>Stage</th><th>Event in → out</th><th>Latency</th><th>Status</th><th>Error</th></tr></thead>
    <tbody>
{"".join(rows)}
    </tbody>
  </table>

  <h2>Redis stream counters (queue depth / lag)</h2>
  <table>
    <thead><tr><th>Stream</th><th>Published</th><th>Delivered</th><th>In flight</th><th>Max in flight</th></tr></thead>
    <tbody>
{counters_body}
    </tbody>
  </table>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full pipeline with Redis Streams and emit metrics")
    parser.add_argument("--redis-url", default=os.getenv("REDIS_URL"), help="Redis URL (default: REDIS_URL)")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "agents" / "eval", help="Output directory for JSON/HTML")
    args = parser.parse_args()

    redis_url = args.redis_url
    if not redis_url:
        print("Error: set REDIS_URL or pass --redis-url (e.g. redis://localhost:6379/0)")
        return 1

    try:
        result = _run(redis_url, args.output_dir)
    except RedisDependencyError as e:
        print(f"Error: {e}")
        return 1
    except RedisStreamsError as e:
        print(f"Redis error: {e}")
        return 1

    json_path = args.output_dir / "full_pipeline_redis_metrics.json"
    html_path = args.output_dir / "full_pipeline_redis_metrics.html"
    _write_json(result, json_path)
    _write_html(result, html_path)

    print(f"Metrics written to {json_path}")
    print(f"Report written to {html_path}")
    print(f"Open in browser: file://{html_path.resolve()}")
    if not result.get("success"):
        print("Pipeline had one or more stage failures; check the HTML report to locate the error.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
