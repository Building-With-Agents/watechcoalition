"""
Week 2 Journey Dashboard (Streamlit).

Usage:
    streamlit run agents/dashboard/streamlit_app.py

Features:
- Run the walking-skeleton pipeline in-process.
- Load the last saved event journey from disk.
- Visualize one record's end-to-end event chain with correlation tracking.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from agents.common.pipeline.runner import run_pipeline

AGENTS_ROOT = Path(__file__).resolve().parents[1]
EVENT_CACHE_PATH = AGENTS_ROOT / "data" / "rendered" / "last_pipeline_events.json"
PIPELINE_FIXTURE_PATH = AGENTS_ROOT / "data" / "fixtures" / "fallback_scrape_sample.json"
STAGING_SAMPLE_PATH = AGENTS_ROOT / "data" / "staging" / "raw_scrape_sample.json"
EXPECTED_STAGE_COUNT = 6

st.set_page_config(
    page_title="Job Intelligence Engine Journey",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
  font-family: "Space Grotesk", sans-serif;
}

.stApp {
  background: radial-gradient(circle at 15% 10%, #f4f9ff 0%, #f0f7f4 35%, #f8f5eb 100%);
}

.journey-card {
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(15, 23, 42, 0.09);
  padding: 0.9rem 1rem;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.journey-label {
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #475569;
  margin-bottom: 0.2rem;
}

.journey-value {
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
}

.event-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
}

.event-subtitle {
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.78rem;
  color: #475569;
}
</style>
    """,
    unsafe_allow_html=True,
)


def _safe_json_load(path: Path) -> Any:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _save_events(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=True, indent=2)


def _resolve_user_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (Path.cwd() / candidate).resolve()


def _normalize_events(events: Any) -> list[dict[str, Any]]:
    if not isinstance(events, list):
        return []

    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(events, start=1):
        if not isinstance(raw, dict):
            continue
        payload = raw.get("payload")
        normalized.append(
            {
                "stage_index": index,
                "agent_id": str(raw.get("agent_id", "unknown")),
                "event_id": str(raw.get("event_id", "missing-event-id")),
                "correlation_id": str(raw.get("correlation_id", "missing-correlation-id")),
                "timestamp": str(raw.get("timestamp", "")),
                "schema_version": str(raw.get("schema_version", "unknown")),
                "payload": payload if isinstance(payload, dict) else {},
            }
        )
    return normalized


def _parse_iso_timestamp(timestamp: str) -> datetime | None:
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def _summarize_payload(payload: dict[str, Any]) -> str:
    if not payload:
        return "No payload"
    if "status" in payload:
        return f"status={payload.get('status')}"
    if isinstance(payload.get("jobs"), list):
        jobs = payload.get("jobs", [])
        if jobs and isinstance(jobs[0], dict):
            first = jobs[0]
            title = first.get("title", "unknown title")
            company = first.get("company", "unknown company")
            return f"{len(jobs)} job(s), first: {title} @ {company}"
        return f"{len(jobs)} job(s)"
    if "total_postings" in payload:
        return f"total_postings={payload.get('total_postings')}"
    if "top_skills" in payload and isinstance(payload["top_skills"], list):
        return f"top_skills={len(payload['top_skills'])}"
    keys = ", ".join(sorted(payload.keys())[:4])
    return f"keys: {keys or 'none'}"


def _first_job_snapshot(events: list[dict[str, Any]]) -> dict[str, Any]:
    for event in events:
        jobs = event["payload"].get("jobs")
        if isinstance(jobs, list) and jobs and isinstance(jobs[0], dict):
            return jobs[0]
    return {}


def _build_event_table(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    prior_ts: datetime | None = None
    for event in events:
        ts = _parse_iso_timestamp(event["timestamp"])
        delta_ms: int | None = None
        if ts and prior_ts:
            delta_ms = max(int((ts - prior_ts).total_seconds() * 1000), 0)
        rows.append(
            {
                "stage": event["stage_index"],
                "agent": event["agent_id"],
                "event_id": event["event_id"],
                "timestamp": event["timestamp"] or "unknown",
                "delta_ms": delta_ms,
                "summary": _summarize_payload(event["payload"]),
            }
        )
        if ts:
            prior_ts = ts
    return rows


def _run_pipeline_and_cache(
    output_path: Path,
    skip_health_check: bool,
) -> list[dict[str, Any]]:
    events = run_pipeline(skip_health_check=skip_health_check)
    _save_events(output_path, events)
    return events


def _load_records(path: Path) -> list[dict[str, Any]]:
    data = _safe_json_load(path)
    if isinstance(data, list):
        return [entry for entry in data if isinstance(entry, dict)]
    return []


if "journey_events" not in st.session_state:
    cached = _safe_json_load(EVENT_CACHE_PATH)
    st.session_state.journey_events = _normalize_events(cached)

st.title("Job Intelligence Engine")
st.subheader("Week 2 Walking Skeleton Journey Dashboard")

with st.sidebar:
    st.header("Journey Controls")
    run_now = st.button("Run Pipeline Now", type="primary", use_container_width=True)
    skip_health_check = st.toggle(
        "Skip health checks before run",
        value=False,
        help="Use for faster local iteration. Leave off for readiness validation.",
    )
    saved_path_input = st.text_input("Journey JSON path", value=str(EVENT_CACHE_PATH))
    selected_events_path = _resolve_user_path(saved_path_input)
    load_saved = st.button("Load Journey from Path", use_container_width=True)
    uploaded_events_file = st.file_uploader("Or upload journey JSON", type=["json"])
    show_payload_json = st.toggle("Show full payload JSON", value=False)
    st.caption(f"Resolved journey path: `{selected_events_path}`")

if run_now:
    with st.spinner("Running walking skeleton pipeline..."):
        st.session_state.journey_events = _normalize_events(
            _run_pipeline_and_cache(selected_events_path, skip_health_check)
        )
if load_saved:
    st.session_state.journey_events = _normalize_events(_safe_json_load(selected_events_path))
if uploaded_events_file is not None:
    try:
        uploaded = json.loads(uploaded_events_file.getvalue().decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        st.error("Uploaded file is not valid UTF-8 JSON.")
    else:
        st.session_state.journey_events = _normalize_events(uploaded)

tab_journey, tab_fixtures = st.tabs(["Journey View", "Raw Fixture Explorer"])

with tab_journey:
    events = st.session_state.journey_events
    if not events:
        st.warning(
            "No journey events found. Run the pipeline from the sidebar or use "
            f"`python -m agents.run_pipeline --save-events {selected_events_path}`."
        )
    else:
        correlation_ids = {event["correlation_id"] for event in events}
        if len(correlation_ids) > 1:
            st.error("Event list contains multiple correlation_ids; expected exactly one run journey.")

        correlation_id = events[0]["correlation_id"] if events else "unknown"
        completion_pct = min(len(events) / EXPECTED_STAGE_COUNT, 1.0)
        first_job = _first_job_snapshot(events)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(
                f"""
<div class="journey-card">
  <div class="journey-label">Correlation ID</div>
  <div class="journey-value">{correlation_id}</div>
</div>
                """,
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f"""
<div class="journey-card">
  <div class="journey-label">Stages Completed</div>
  <div class="journey-value">{len(events)} / {EXPECTED_STAGE_COUNT}</div>
</div>
                """,
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                f"""
<div class="journey-card">
  <div class="journey-label">Schema Version</div>
  <div class="journey-value">{events[-1]["schema_version"]}</div>
</div>
                """,
                unsafe_allow_html=True,
            )
        with m4:
            status = events[-1]["payload"].get("status", "in_progress")
            st.markdown(
                f"""
<div class="journey-card">
  <div class="journey-label">Run Status</div>
  <div class="journey-value">{status}</div>
</div>
                """,
                unsafe_allow_html=True,
            )

        st.progress(completion_pct, text=f"Journey completion: {int(completion_pct * 100)}%")

        if first_job:
            st.markdown("### Record Snapshot")
            c1, c2, c3 = st.columns(3)
            c1.metric("Title", str(first_job.get("title", "unknown")))
            c2.metric("Company", str(first_job.get("company", "unknown")))
            c3.metric("Location", str(first_job.get("location", "unknown")))

        st.markdown("### Event Timeline")
        for event in events:
            summary = _summarize_payload(event["payload"])
            st.markdown(
                f"""
<div class="journey-card">
  <div class="event-title">Stage {event["stage_index"]}: {event["agent_id"]}</div>
  <div class="event-subtitle">event_id={event["event_id"]} | {event["timestamp"]}</div>
  <div style="margin-top: 0.4rem;">{summary}</div>
</div>
                """,
                unsafe_allow_html=True,
            )
            if show_payload_json:
                st.json(event["payload"])
            st.write("")

        st.markdown("### Journey Table")
        st.dataframe(_build_event_table(events), use_container_width=True, hide_index=True)

with tab_fixtures:
    source_labels = {
        "Week 2 pipeline fixture": PIPELINE_FIXTURE_PATH,
        "Week 1 staging scrape sample": STAGING_SAMPLE_PATH,
    }
    selected_source_label = st.radio(
        "Fixture source",
        options=list(source_labels),
        horizontal=True,
    )
    selected_source_path = source_labels[selected_source_label]
    records = _load_records(selected_source_path)
    if not records:
        st.info(
            f"No records found at `{selected_source_path}`."
        )
    else:
        sources = sorted({str(r.get("source", "unknown")) for r in records})
        selected_sources = st.multiselect("Source filter", options=sources, default=sources)
        filtered = [r for r in records if str(r.get("source", "unknown")) in selected_sources]
        st.caption(f"Showing {len(filtered)} of {len(records)} fixture postings")
        for index, record in enumerate(filtered, start=1):
            title = str(record.get("title", "Untitled"))
            company = str(record.get("company", "Unknown company"))
            location = str(record.get("location", "Unknown location"))
            with st.expander(f"{index}. {title} — {company}", expanded=False):
                st.markdown(f"**Location:** {location}")
                st.markdown(f"**URL:** {record.get('url', '—')}")
                st.markdown(f"**Timestamp:** {record.get('timestamp', '—')}")
                raw_text = str(record.get("raw_text", ""))
                st.text(raw_text[:550] + ("..." if len(raw_text) > 550 else ""))
