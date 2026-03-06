"""
Demo dashboard for the Job Intelligence Engine pipeline.

Walkthrough pages:
1. Pipeline Run Summary
2. Record Journey
3. Batch Insights

Usage:
    streamlit run agents/dashboard/streamlit_app.py
"""
# ruff: noqa: E402

from __future__ import annotations

import html
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Ensure repo root is on path so "agents" package is importable when Streamlit runs this file.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd
import streamlit as st

from agents.common.events.base import AgentEvent
from agents.common.pipeline.runner import run_pipeline
from agents.demand_analysis.agent import DemandAnalysisAgent
from agents.orchestration.agent import OrchestrationAgent

AGENTS_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = AGENTS_ROOT / "data"
RENDERED_ROOT = DATA_ROOT / "rendered"
EVENT_CACHE_PATH = RENDERED_ROOT / "last_pipeline_events.json"
RUN_HISTORY_PATH = RENDERED_ROOT / "pipeline_run_history.json"

PIPELINE_FIXTURE_PATH = DATA_ROOT / "fixtures" / "fallback_scrape_sample.json"
SKILLS_FIXTURE_PATH = DATA_ROOT / "fixtures" / "fixture_skills_extracted.json"
ENRICHED_FIXTURE_PATH = DATA_ROOT / "fixtures" / "fixture_enriched.json"

STAGE_ORDER = [
    "orchestration",
    "ingestion",
    "normalization",
    "skills_extraction",
    "enrichment",
    "analytics",
    "demand_analysis",
    "visualization",
]

STAGE_LABELS = {
    "orchestration": "Orchestration",
    "ingestion": "Ingestion",
    "normalization": "Normalization",
    "skills_extraction": "Skills Extraction",
    "enrichment": "Enrichment",
    "analytics": "Analytics",
    "demand_analysis": "Demand Analysis",
    "visualization": "Visualization",
}

STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_MISSING = "missing"

FAIL_TOKENS = {"failed", "error", "down", "timeout", "aborted"}

st.set_page_config(page_title="Pipeline Demo Dashboard", layout="wide")

st.markdown(
    """
<style>
.app-title-card {
  border: 1px solid #d5dde8;
  border-radius: 12px;
  background: linear-gradient(135deg, #f6f8fb 0%, #ffffff 100%);
  padding: 1.1rem 1.2rem;
  margin: 0.12rem 0 0.85rem 0;
}
.app-title-chip {
  display: inline-block;
  font-size: 0.92rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #285680;
  background: #e6eef7;
  border: 1px solid #c8d8eb;
  border-radius: 999px;
  padding: 0.28rem 0.85rem;
  margin-bottom: 0.48rem;
}
.app-title-text {
  font-size: 3.2rem !important;
  font-weight: 700;
  color: #1c2d3f;
  margin: 0;
  line-height: 1.1;
}
.title-metrics-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-top: 0.65rem;
}
.title-metric-pill {
  display: inline-block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #23425f;
  background: #edf4fd;
  border: 1px solid #cdddf1;
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
}
[data-testid="stMetric"] {
  background: #f7fbff;
  border: 1px solid #d4e2f2;
  border-radius: 10px;
  padding: 0.45rem 0.6rem;
}
[data-testid="stMetricLabel"] {
  font-weight: 600;
  color: #36526e;
}
[data-testid="stMetricValue"] {
  color: #1a3550;
}
[data-testid="stAppViewContainer"] h2 {
  font-size: 1.65rem !important;
  line-height: 1.2 !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


def _render_title_card_with_metrics(title: str, metrics: list[tuple[str, str]]) -> None:
    metric_html = "".join(
        f'<span class="title-metric-pill">{html.escape(label)}: {html.escape(value)}</span>'
        for label, value in metrics
    )
    st.markdown(
        f"""
<div class="app-title-card">
  <div class="app-title-chip">Dashboard</div>
  <p class="app-title-text">{html.escape(title)}</p>
  <div class="title-metrics-row">{metric_html}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _safe_json_load(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2)


def _resolve_user_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (Path.cwd() / candidate).resolve()


def _parse_iso_timestamp(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _as_event(raw: dict[str, Any]) -> AgentEvent | None:
    ts = _parse_iso_timestamp(str(raw.get("timestamp", "")))
    if ts is None:
        return None
    payload = raw.get("payload")
    return AgentEvent(
        event_id=str(raw.get("event_id", "missing-event-id")),
        correlation_id=str(raw.get("correlation_id", "missing-correlation-id")),
        agent_id=str(raw.get("agent_id", "unknown")),
        timestamp=ts,
        schema_version=str(raw.get("schema_version", "1.0")),
        payload=payload if isinstance(payload, dict) else {},
    )


def _derive_stage_status(payload: dict[str, Any], has_event: bool) -> str:
    if not has_event:
        return STATUS_MISSING

    candidates = [
        payload.get("status"),
        payload.get("extraction_status"),
        payload.get("enrichment_status"),
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip().lower() in FAIL_TOKENS:
            return STATUS_FAILED

    return STATUS_COMPLETED


def _to_stage_event(raw: dict[str, Any], stage_id: str, stage_index: int) -> dict[str, Any]:
    payload = raw.get("payload")
    parsed_payload = payload if isinstance(payload, dict) else {}
    return {
        "stage_index": stage_index,
        "stage_id": stage_id,
        "stage_label": STAGE_LABELS[stage_id],
        "agent_id": str(raw.get("agent_id", stage_id)),
        "event_id": str(raw.get("event_id", f"missing-{stage_id}")),
        "correlation_id": str(raw.get("correlation_id", "missing-correlation-id")),
        "timestamp": str(raw.get("timestamp", "")),
        "schema_version": str(raw.get("schema_version", "1.0")),
        "payload": parsed_payload,
        "stage_status": _derive_stage_status(parsed_payload, has_event=True),
        "is_placeholder": False,
    }


def _missing_stage_event(stage_id: str, stage_index: int, correlation_id: str) -> dict[str, Any]:
    return {
        "stage_index": stage_index,
        "stage_id": stage_id,
        "stage_label": STAGE_LABELS[stage_id],
        "agent_id": stage_id,
        "event_id": f"missing-{stage_id}",
        "correlation_id": correlation_id,
        "timestamp": "",
        "schema_version": "1.0",
        "payload": {},
        "stage_status": STATUS_MISSING,
        "is_placeholder": True,
    }


def _normalize_to_eight_stages(events: Any) -> list[dict[str, Any]]:
    if not isinstance(events, list):
        return []

    by_stage: dict[str, dict[str, Any]] = {}
    correlation_id = "missing-correlation-id"

    for raw in events:
        if not isinstance(raw, dict):
            continue
        stage_id = str(raw.get("agent_id", ""))
        if stage_id not in STAGE_ORDER:
            continue
        by_stage[stage_id] = raw
        if correlation_id == "missing-correlation-id":
            correlation_id = str(raw.get("correlation_id", correlation_id))

    normalized: list[dict[str, Any]] = []
    for index, stage_id in enumerate(STAGE_ORDER, start=1):
        raw = by_stage.get(stage_id)
        if raw is None:
            normalized.append(_missing_stage_event(stage_id, index, correlation_id))
        else:
            normalized.append(_to_stage_event(raw, stage_id, index))

    return normalized


def _run_pipeline_with_eight_stages(skip_health_check: bool) -> list[dict[str, Any]]:
    core_events = run_pipeline(skip_health_check=skip_health_check)
    if not core_events:
        return []

    correlation_id = str(core_events[0].get("correlation_id", "missing-correlation-id"))
    by_stage: dict[str, dict[str, Any]] = {}
    for raw in core_events:
        if isinstance(raw, dict):
            stage_id = str(raw.get("agent_id", ""))
            if stage_id in STAGE_ORDER:
                by_stage[stage_id] = raw

    orchestration = OrchestrationAgent().process(None, correlation_id=correlation_id)
    if orchestration is not None:
        by_stage["orchestration"] = orchestration.to_dict()

    analytics_event = by_stage.get("analytics")
    demand_event: dict[str, Any] | None = None
    if analytics_event is not None:
        analytics_agent_event = _as_event(analytics_event)
        if analytics_agent_event is not None:
            demand = DemandAnalysisAgent().process(analytics_agent_event)
            if demand is not None:
                demand_event = demand.to_dict()

    if demand_event is not None:
        by_stage["demand_analysis"] = demand_event

    merged: list[dict[str, Any]] = []
    for stage_id in STAGE_ORDER:
        raw = by_stage.get(stage_id)
        if raw is not None:
            merged.append(raw)

    return _normalize_to_eight_stages(merged)


def _load_records(path: Path) -> list[dict[str, Any]]:
    raw = _safe_json_load(path)
    if isinstance(raw, list):
        return [entry for entry in raw if isinstance(entry, dict)]
    return []


def _load_history() -> list[dict[str, Any]]:
    raw = _safe_json_load(RUN_HISTORY_PATH)
    if not isinstance(raw, list):
        return []

    history: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        events = _normalize_to_eight_stages(entry.get("events"))
        if not events:
            continue
        history.append(
            {
                "run_id": str(entry.get("run_id", events[0]["correlation_id"])),
                "created_at": str(entry.get("created_at", "")),
                "source": str(entry.get("source", "unknown")),
                "events": events,
            }
        )

    history.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return history


def _save_history(history: list[dict[str, Any]]) -> None:
    serializable = [
        {
            "run_id": run["run_id"],
            "created_at": run["created_at"],
            "source": run["source"],
            "events": run["events"],
        }
        for run in history
    ]
    _save_json(RUN_HISTORY_PATH, serializable)


def _append_run_to_history(
    history: list[dict[str, Any]],
    events: list[dict[str, Any]],
    source: str,
) -> list[dict[str, Any]]:
    if not events:
        return history

    run_id = events[0]["correlation_id"]
    entry = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "source": source,
        "events": events,
    }

    deduped = [run for run in history if run.get("run_id") != run_id]
    deduped.insert(0, entry)
    return deduped[:50]


def _extract_record_ids(events: list[dict[str, Any]]) -> list[str]:
    record_ids: set[str] = set()
    for event in events:
        payload = event.get("payload", {})
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(jobs, list):
            continue
        for job in jobs:
            if not isinstance(job, dict):
                continue
            posting_id = job.get("posting_id")
            if posting_id is not None:
                record_ids.add(str(posting_id))

    if record_ids:
        return sorted(record_ids)

    correlation_id = events[0]["correlation_id"] if events else "unknown"
    return [f"run:{correlation_id}"]


def _stage_event_for_record(
    stage_id: str,
    record_id: str,
    events_by_stage: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    event = events_by_stage.get(stage_id)
    if event is None:
        return _missing_stage_event(stage_id, STAGE_ORDER.index(stage_id) + 1, "missing-correlation-id")

    payload = event.get("payload", {})
    jobs = payload.get("jobs") if isinstance(payload, dict) else None
    if isinstance(jobs, list) and jobs:
        matches_record = False
        for job in jobs:
            if isinstance(job, dict) and str(job.get("posting_id", "")) == record_id:
                matches_record = True
                break
        if not matches_record:
            missing = _missing_stage_event(stage_id, event["stage_index"], event["correlation_id"])
            return missing

    return event


def _build_record_status_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        events = run["events"]
        by_stage = {event["stage_id"]: event for event in events}
        for record_id in _extract_record_ids(events):
            row: dict[str, Any] = {
                "run_id": run["run_id"],
                "created_at": run["created_at"],
                "record_id": record_id,
            }
            non_completed = 0
            for stage_id in STAGE_ORDER:
                stage_event = _stage_event_for_record(stage_id, record_id, by_stage)
                status = stage_event["stage_status"]
                if status != STATUS_COMPLETED:
                    non_completed += 1
                row[STAGE_LABELS[stage_id]] = status
            row["non_completed_stages"] = non_completed
            rows.append(row)
    return rows


def _run_level_counts(events: list[dict[str, Any]]) -> Counter:
    return Counter(event.get("stage_status", STATUS_MISSING) for event in events)


def _run_state(events: list[dict[str, Any]]) -> str:
    counts = _run_level_counts(events)
    if counts[STATUS_FAILED] > 0:
        return "failed"
    if counts[STATUS_MISSING] > 0:
        return "partial"
    return "completed"


def _summary_for_runs(runs: list[dict[str, Any]]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for run in runs:
        counts = _run_level_counts(run["events"])
        records.append(
            {
                "run_id": run["run_id"],
                "created_at": run["created_at"],
                "source": run["source"],
                "state": _run_state(run["events"]),
                "completed": counts[STATUS_COMPLETED],
                "failed": counts[STATUS_FAILED],
                "missing": counts[STATUS_MISSING],
                "records_detected": len(_extract_record_ids(run["events"])),
            }
        )
    return pd.DataFrame(records)


def _payload_summary(payload: dict[str, Any]) -> str:
    if not payload:
        return "No payload"
    if "status" in payload:
        return f"status={payload.get('status')}"
    if isinstance(payload.get("jobs"), list):
        return f"jobs={len(payload.get('jobs', []))}"
    if "total_postings" in payload:
        return f"total_postings={payload.get('total_postings')}"
    keys = ", ".join(sorted(payload.keys())[:4])
    return f"keys: {keys if keys else 'none'}"


def _relevant_payload_fields(payload: dict[str, Any], record_id: str) -> dict[str, Any]:
    if not payload:
        return {}

    jobs = payload.get("jobs")
    if isinstance(jobs, list):
        for job in jobs:
            if isinstance(job, dict) and str(job.get("posting_id", "")) == record_id:
                keys = [
                    "posting_id",
                    "title",
                    "company",
                    "location",
                    "extraction_status",
                    "enrichment_status",
                    "quality_score",
                    "spam_score",
                ]
                return {k: job.get(k) for k in keys if k in job}

    keys = [
        "status",
        "record_count",
        "total_postings",
        "upstream_agent_id",
        "observed_agent_id",
        "avg_quality_score",
        "avg_spam_score",
    ]
    reduced = {k: payload.get(k) for k in keys if k in payload}
    if reduced:
        return reduced

    first_keys = sorted(payload.keys())[:8]
    return {k: payload.get(k) for k in first_keys}


def _detect_anomalies(enriched_records: list[dict[str, Any]]) -> pd.DataFrame:
    if not enriched_records:
        return pd.DataFrame()

    quality_values = [float(r.get("quality_score", 0.0)) for r in enriched_records if r.get("quality_score") is not None]
    spam_values = [float(r.get("spam_score", 0.0)) for r in enriched_records if r.get("spam_score") is not None]
    if not quality_values or not spam_values:
        return pd.DataFrame()

    quality_mean = sum(quality_values) / len(quality_values)
    spam_mean = sum(spam_values) / len(spam_values)
    quality_std = (sum((v - quality_mean) ** 2 for v in quality_values) / len(quality_values)) ** 0.5
    spam_std = (sum((v - spam_mean) ** 2 for v in spam_values) / len(spam_values)) ** 0.5

    anomalies: list[dict[str, Any]] = []
    for rec in enriched_records:
        quality = float(rec.get("quality_score", 0.0))
        spam = float(rec.get("spam_score", 0.0))
        low_quality = quality_std > 0 and quality < quality_mean - (1.5 * quality_std)
        high_spam = spam_std > 0 and spam > spam_mean + (1.5 * spam_std)
        if low_quality or high_spam:
            anomalies.append(
                {
                    "posting_id": rec.get("posting_id"),
                    "title": rec.get("title", "unknown"),
                    "quality_score": quality,
                    "spam_score": spam,
                    "flags": ", ".join(
                        part for part in ["low_quality" if low_quality else "", "high_spam" if high_spam else ""] if part
                    ),
                }
            )

    return pd.DataFrame(anomalies)


def _batch_records_from_run(run: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract job-level records from run events for missing-fields / batch analysis. Prefer normalization, then ingestion."""
    events = run.get("events") or []
    for stage_id in ("normalization", "ingestion"):
        ev = next((e for e in events if e.get("stage_id") == stage_id), None)
        if ev is None:
            continue
        jobs = (ev.get("payload") or {}).get("jobs")
        if isinstance(jobs, list) and jobs:
            return [j for j in jobs if isinstance(j, dict)]
    return []


def _skills_records_from_run(run: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract records with skills from run (skills_extraction payload.jobs)."""
    ev = next((e for e in (run.get("events") or []) if e.get("stage_id") == "skills_extraction"), None)
    if ev is None:
        return []
    jobs = (ev.get("payload") or {}).get("jobs")
    if not isinstance(jobs, list):
        return []
    return [j for j in jobs if isinstance(j, dict)]


def _enriched_records_from_run(run: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract enriched job records from run (enrichment payload.jobs) for quality/spam analysis."""
    ev = next((e for e in (run.get("events") or []) if e.get("stage_id") == "enrichment"), None)
    if ev is None:
        return []
    jobs = (ev.get("payload") or {}).get("jobs")
    if not isinstance(jobs, list):
        return []
    return [j for j in jobs if isinstance(j, dict)]


def _history_quality_trend(history: list[dict[str, Any]]) -> pd.DataFrame:
    points: list[dict[str, Any]] = []
    for run in history:
        analytics = next((e for e in run["events"] if e["stage_id"] == "analytics"), None)
        if analytics is None:
            continue
        payload = analytics.get("payload", {})
        avg_quality = payload.get("avg_quality_score") if isinstance(payload, dict) else None
        if avg_quality is None:
            continue
        points.append(
            {
                "created_at": run.get("created_at", ""),
                "avg_quality_score": float(avg_quality),
                "run_id": run["run_id"],
            }
        )

    if not points:
        return pd.DataFrame()

    df = pd.DataFrame(points)
    df = df.sort_values("created_at")
    return df


def _bootstrap_state() -> None:
    if "run_history" not in st.session_state:
        st.session_state.run_history = _load_history()

    if "current_events" not in st.session_state:
        cached = _safe_json_load(EVENT_CACHE_PATH)
        normalized = _normalize_to_eight_stages(cached)
        st.session_state.current_events = normalized
        if normalized:
            st.session_state.run_history = _append_run_to_history(
                st.session_state.run_history,
                normalized,
                source="cache",
            )
            _save_history(st.session_state.run_history)


_bootstrap_state()

with st.sidebar:
    st.subheader("Run Pipeline")
    run_now = st.button("Run pipeline", type="primary", width="stretch")
    skip_health_check = st.toggle("Skip health checks", value=False)

    st.divider()
    st.subheader("Load Data")
    with st.expander("Load existing run", expanded=False):
        saved_path_input = st.text_input("Run JSON path", value=str(EVENT_CACHE_PATH))
        selected_events_path = _resolve_user_path(saved_path_input)
        load_saved = st.button("Load from path", width="stretch")
        uploaded_events_file = st.file_uploader("Upload run JSON", type=["json"])
        st.code(str(selected_events_path), language="text")

    st.divider()
    st.subheader("About")
    st.caption(f"Run history file: `{RUN_HISTORY_PATH}`")

if run_now:
    with st.spinner("Running pipeline..."):
        events = _run_pipeline_with_eight_stages(skip_health_check)
        st.session_state.current_events = events
        _save_json(selected_events_path, events)
        _save_json(EVENT_CACHE_PATH, events)
        st.session_state.run_history = _append_run_to_history(
            st.session_state.run_history,
            events,
            source="run_pipeline",
        )
        _save_history(st.session_state.run_history)

if load_saved:
    loaded = _safe_json_load(selected_events_path)
    events = _normalize_to_eight_stages(loaded)
    st.session_state.current_events = events
    st.session_state.run_history = _append_run_to_history(
        st.session_state.run_history,
        events,
        source="loaded_path",
    )
    _save_history(st.session_state.run_history)

if uploaded_events_file is not None:
    try:
        uploaded = json.loads(uploaded_events_file.getvalue().decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        st.error("Uploaded file is not valid UTF-8 JSON.")
    else:
        events = _normalize_to_eight_stages(uploaded)
        st.session_state.current_events = events
        st.session_state.run_history = _append_run_to_history(
            st.session_state.run_history,
            events,
            source="uploaded_json",
        )
        _save_history(st.session_state.run_history)

history: list[dict[str, Any]] = st.session_state.run_history
if not history and st.session_state.current_events:
    history = _append_run_to_history([], st.session_state.current_events, source="session")

if history:
    _top_df = _summary_for_runs(history)
    _title_metrics = [
        ("Runs", str(len(history))),
        ("Completed", str(int((_top_df["state"] == "completed").sum()))),
        ("Failed", str(int((_top_df["state"] == "failed").sum()))),
        ("Partial", str(int((_top_df["state"] == "partial").sum()))),
    ]
else:
    _title_metrics = [("Runs", "0"), ("Completed", "0"), ("Failed", "0"), ("Partial", "0")]
_render_title_card_with_metrics("Job Intelligence Engine", _title_metrics)

summary_tab, journey_tab, insights_tab = st.tabs(
    ["Pipeline Run Summary", "Record Journey", "Batch Insights"]
)

with summary_tab:
    st.header("Pipeline Run Summary")
    if not history:
        st.info("No runs yet. Run the pipeline from the sidebar.")
    else:
        with st.expander("Scope and Filters", expanded=True):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                latest_only = st.toggle("Latest run only", value=True)
            with c2:
                failed_only = st.toggle("Failed-only records", value=False)
            with c3:
                max_records = st.slider("Record count", min_value=1, max_value=200, value=25)

        visible_runs = history[:1] if latest_only else history
        summary_df = _summary_for_runs(visible_runs)
        st.subheader("Stage Health (Latest Run)")
        latest_counts = _run_level_counts(visible_runs[0]["events"])
        c_counts1, c_counts2, c_counts3 = st.columns(3)
        c_counts1.metric("Completed stages", latest_counts[STATUS_COMPLETED])
        c_counts2.metric("Failed stages", latest_counts[STATUS_FAILED])
        c_counts3.metric("Missing stages", latest_counts[STATUS_MISSING])

        st.subheader("Stage Breakdown")
        chart_df = pd.DataFrame(
            {
                "status": ["completed", "failed", "missing"],
                "count": [
                    latest_counts[STATUS_COMPLETED],
                    latest_counts[STATUS_FAILED],
                    latest_counts[STATUS_MISSING],
                ],
            }
        ).set_index("status")
        st.bar_chart(chart_df)
        st.divider()

        st.subheader("Per-Record Stage Matrix")
        record_rows = _build_record_status_rows(visible_runs)
        if failed_only:
            record_rows = [row for row in record_rows if row["non_completed_stages"] > 0]

        record_rows = record_rows[:max_records]
        if not record_rows:
            st.info("No matching records for current filters.")
        else:
            matrix_columns = (
                ["run_id", "created_at", "record_id"]
                + [STAGE_LABELS[stage_id] for stage_id in STAGE_ORDER]
                + ["non_completed_stages"]
            )
            matrix_df = pd.DataFrame(record_rows)
            matrix_df = matrix_df[[col for col in matrix_columns if col in matrix_df.columns]]
            st.dataframe(matrix_df, width="stretch", hide_index=True)

        st.subheader("Run List")
        run_list_cols = [
            "run_id",
            "created_at",
            "state",
            "source",
            "records_detected",
            "completed",
            "failed",
            "missing",
        ]
        summary_df = summary_df[[col for col in run_list_cols if col in summary_df.columns]]
        st.dataframe(summary_df, width="stretch", hide_index=True)

with journey_tab:
    st.header("Record Journey")
    if not history:
        st.info("No runs yet. Run the pipeline from the sidebar.")
    else:
        with st.expander("Select Run and Record", expanded=True):
            run_options = [run["run_id"] for run in history]
            select_col1, select_col2 = st.columns(2)
            with select_col1:
                selected_run_id = st.selectbox(
                    "Run (correlation ID)",
                    options=run_options,
                    index=0,
                    help="Select the pipeline run to inspect.",
                )
            selected_run = next(run for run in history if run["run_id"] == selected_run_id)

            record_ids = _extract_record_ids(selected_run["events"])
            with select_col2:
                selected_record_id = st.selectbox(
                    "Record",
                    options=record_ids,
                    index=0,
                    help="Select one record within the run.",
                )

        events_by_stage = {event["stage_id"]: event for event in selected_run["events"]}

        journey_events: list[dict[str, Any]] = []
        journey_rows: list[dict[str, Any]] = []
        for stage_id in STAGE_ORDER:
            stage_event = _stage_event_for_record(stage_id, selected_record_id, events_by_stage)
            journey_events.append(stage_event)
            journey_rows.append(
                {
                    "stage": stage_event["stage_index"],
                    "agent": stage_event["stage_label"],
                    "status": stage_event["stage_status"],
                    "timestamp": stage_event["timestamp"] or "missing",
                    "event_id": stage_event["event_id"],
                    "summary": _payload_summary(stage_event["payload"]),
                }
            )

        st.subheader("8-Stage Timeline")
        st.dataframe(pd.DataFrame(journey_rows), width="stretch", hide_index=True)

        first_problem = next(
            (event for event in journey_events if event["stage_status"] in {STATUS_FAILED, STATUS_MISSING}),
            None,
        )

        st.subheader("Failure Details")
        if first_problem is None:
            st.info("All stages are completed for this record.")
        else:
            stage_name = first_problem["stage_label"]
            st.error(f"First non-completed stage: {stage_name}")
            if first_problem.get("is_placeholder") or first_problem.get("stage_status") == STATUS_MISSING:
                st.warning("Status: missing. Stage did not run (no event for this stage).")
            else:
                relevant = _relevant_payload_fields(first_problem["payload"], selected_record_id)
                if relevant:
                    st.json(relevant)
                else:
                    st.info("Status: failed. No payload details are available for this stage.")

with insights_tab:
    st.header("Batch Insights")
    if not history:
        st.info("No runs yet. Run the pipeline from the sidebar.")
    else:
        latest_run = history[0]
        latest_events = latest_run["events"]
        latest_state = _run_state(latest_events)

        analytics_event = next((e for e in latest_events if e["stage_id"] == "analytics"), None)
        analytics_payload = analytics_event["payload"] if analytics_event else {}

        raw_records = _batch_records_from_run(latest_run)
        if not raw_records:
            raw_records = _load_records(PIPELINE_FIXTURE_PATH)

        skills_records = _skills_records_from_run(latest_run)
        if not skills_records:
            skills_records = _load_records(SKILLS_FIXTURE_PATH)

        enriched_records = _enriched_records_from_run(latest_run)
        if not enriched_records:
            enriched_records = _load_records(ENRICHED_FIXTURE_PATH)

        st.subheader("Pipeline Health")
        if latest_state == "completed":
            st.success("Pipeline stages completed across all 8 stages for latest run.")
        elif latest_state == "partial":
            st.warning("Latest run is partial: one or more stages are missing.")
        else:
            st.error("Latest run has failed stages.")

        st.subheader("Output Quality")
        if isinstance(analytics_payload, dict):
            oq1, oq2 = st.columns(2)
            oq1.metric("Average quality score", analytics_payload.get("avg_quality_score", "n/a"))
            oq2.metric("Average spam score", analytics_payload.get("avg_spam_score", "n/a"))
        else:
            st.info("No analytics payload found for output quality metrics.")

        st.subheader("Batch Insight Charts")

        with st.expander("Missing Fields", expanded=True):
            required_fields = ["posting_id", "title", "company", "location", "url", "timestamp", "raw_text"]
            missing_counts: list[dict[str, Any]] = []
            for field in required_fields:
                missing = 0
                for record in raw_records:
                    value = record.get(field)
                    if value is None or (isinstance(value, str) and not value.strip()):
                        missing += 1
                missing_counts.append({"field": field, "missing_count": missing})

            missing_df = pd.DataFrame(missing_counts).set_index("field")
            st.bar_chart(missing_df)

        with st.expander("Extraction Volume", expanded=True):
            extraction_rows: list[dict[str, Any]] = []
            for rec in skills_records:
                skills = rec.get("skills")
                if not isinstance(skills, list):
                    continue
                confidences = [float(s.get("confidence", 0.0)) for s in skills if isinstance(s, dict)]
                extraction_rows.append(
                    {
                        "posting_id": str(rec.get("posting_id", "unknown")),
                        "title": rec.get("title", "unknown"),
                        "skills_count": len(skills),
                        "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
                    }
                )

            extraction_df = pd.DataFrame(extraction_rows)
            if extraction_df.empty:
                st.info("No extraction data available.")
            else:
                st.bar_chart(extraction_df.set_index("posting_id")[["skills_count"]])
                st.dataframe(extraction_df, width="stretch", hide_index=True)

        with st.expander("Anomalies and Drift", expanded=True):
            anomaly_df = _detect_anomalies(enriched_records)
            if anomaly_df.empty:
                st.info("No quality/spam anomalies detected in current batch.")
            else:
                st.dataframe(anomaly_df, width="stretch", hide_index=True)

            trend_df = _history_quality_trend(history)
            if trend_df.empty:
                st.info("Need at least one analytics-bearing run to render drift trend.")
            else:
                st.line_chart(trend_df.set_index("created_at")[["avg_quality_score"]])

        with st.expander("Top Skills", expanded=True):
            top_skills = analytics_payload.get("top_skills") if isinstance(analytics_payload, dict) else None
            if isinstance(top_skills, list) and top_skills:
                skills_df = pd.DataFrame([s for s in top_skills if isinstance(s, dict)])
                if not skills_df.empty and {"skill", "count"}.issubset(skills_df.columns):
                    st.bar_chart(skills_df.set_index("skill")[["count"]].head(10))
            else:
                st.info("No top-skills data available for this run.")
