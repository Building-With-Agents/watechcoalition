from __future__ import annotations

"""
Three-page Streamlit dashboard for the Job Intelligence Engine walking skeleton.

Reads pipeline run data from agents/data/output/pipeline_run.json and provides:
- Page 1: Pipeline Run Summary (records, events, timestamps, stage completion table)
- Page 2: Record Journey (per-correlation_id timeline of 8 stages)
- Page 3: Batch Insights (top skills, seniority distribution, companies/locations from payloads)
"""

import json
from pathlib import Path
from typing import Any

import streamlit as st

# ---- Paths ----
_DASHBOARD_DIR = Path(__file__).resolve().parent
_AGENTS_DIR = _DASHBOARD_DIR.parent
_PIPELINE_RUN_PATH = _AGENTS_DIR / "data" / "output" / "pipeline_run.json"

# Canonical order of the 8 pipeline stages (agent_id values).
STAGE_ORDER = [
    "ingestion",
    "normalization",
    "skills_extraction",
    "enrichment",
    "analytics",
    "visualization",
    "orchestration",
    "demand_analysis",
]


@st.cache_data
def load_pipeline_run() -> list[dict[str, Any]]:
    """
    Load pipeline_run.json from the agents data output directory.

    Returns a list of event dicts (event_id, correlation_id, agent_id, timestamp, payload).
    Cached so repeated page switches do not re-read the file.
    """
    if not _PIPELINE_RUN_PATH.exists():
        return []
    text = _PIPELINE_RUN_PATH.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, list):
        return []
    return data


def _unique_correlation_ids(events: list[dict[str, Any]]) -> list[str]:
    """Return sorted list of unique correlation_id values from the event log."""
    seen: set[str] = set()
    for e in events:
        cid = e.get("correlation_id")
        if cid:
            seen.add(cid)
    return sorted(seen)


def _correlation_id_order(events: list[dict[str, Any]]) -> tuple[list[str], dict[str, str]]:
    """
    Return (ordered_correlation_ids, cid_to_label) where labels are "Record 1", "Record 2", ...
    in the order each correlation_id first appears in the log.
    """
    order: list[str] = []
    seen: set[str] = set()
    for e in events:
        cid = e.get("correlation_id")
        if cid and cid not in seen:
            seen.add(cid)
            order.append(cid)
    labels = {cid: f"Record {i + 1}" for i, cid in enumerate(order)}
    return order, labels


def _event_status(event: dict[str, Any]) -> str:
    """
    Classify event as "ok", "skipped", or "failed" from payload and agent_id.
    All data derived from pipeline_run.json (no hardcoded values).
    """
    payload = event.get("payload") or {}
    agent_id = event.get("agent_id", "")
    stage = payload.get("stage") or ""
    reason = str(payload.get("reason", ""))

    if agent_id == "demand_analysis" and (
        stage == "demand_analysis_skipped" or "phase2" in reason.lower()
    ):
        return "skipped"
    if stage.endswith("_failed") or reason in ("fixture_missing", "invalid_fixture_json"):
        return "failed"
    return "ok"


def _events_for_correlation(events: list[dict[str, Any]], correlation_id: str) -> list[dict[str, Any]]:
    """Return events for the given correlation_id in pipeline stage order."""
    subset = [e for e in events if e.get("correlation_id") == correlation_id]
    # Sort by position in STAGE_ORDER so timeline is correct.
    order_index = {aid: i for i, aid in enumerate(STAGE_ORDER)}
    subset.sort(key=lambda e: order_index.get(e.get("agent_id", ""), 99))
    return subset


def _payload_keys_summary(payload: dict[str, Any]) -> str:
    """Return a short summary of payload keys for display (e.g. 'stage, source_event, sample_raw_record')."""
    if not payload:
        return "—"
    keys = list(payload.keys())[:8]
    return ", ".join(keys) + ("..." if len(payload) > 8 else "")


def _record_dropdown_labels(events: list[dict[str, Any]], ordered_cids: list[str]) -> list[str]:
    """
    Build dropdown labels "Record N — Company: Title" from ingestion payload.sample_raw_record.
    Falls back to "Record N" if title/company not found. Order matches ordered_cids.
    """
    sample_raw_record: list[Any] = []
    for e in events:
        if e.get("agent_id") == "ingestion":
            payload = e.get("payload") or {}
            raw = payload.get("sample_raw_record")
            if isinstance(raw, list) and len(raw) >= len(ordered_cids):
                sample_raw_record = raw
                break

    labels: list[str] = []
    for i, cid in enumerate(ordered_cids):
        base = f"Record {i + 1}"
        if i < len(sample_raw_record) and isinstance(sample_raw_record[i], dict):
            r = sample_raw_record[i]
            company = (r.get("company") or "").strip()
            title = (r.get("title") or "").strip()
            if company or title:
                detail = f"{company}: {title}".strip(": ") if (company and title) else (company or title)
                labels.append(f"{base} — {detail}")
            else:
                labels.append(base)
        else:
            labels.append(base)
    return labels


def render_page_summary(events: list[dict[str, Any]]) -> None:
    """Page 1: Pipeline Run Summary."""
    st.title("Pipeline Run Summary")

    if not events:
        st.warning("No pipeline run data found. Run the pipeline first to generate pipeline_run.json.")
        return

    ordered_cids, cid_to_label = _correlation_id_order(events)
    total_records = len(ordered_cids)
    total_events = len(events)

    # Status counts across all events (from payload/agent_id only)
    status_counts: dict[str, int] = {"ok": 0, "skipped": 0, "failed": 0}
    for e in events:
        status_counts[_event_status(e)] = status_counts.get(_event_status(e), 0) + 1

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total events", total_events)
    with col2:
        st.metric("Unique records", total_records)
    with col3:
        st.metric("OK", status_counts.get("ok", 0))
    with col4:
        st.metric("Skipped", status_counts.get("skipped", 0))
    with col5:
        st.metric("Failed", status_counts.get("failed", 0))

    # Per-agent breakdown: ok / skipped / failed per agent
    st.subheader("Per-agent breakdown")
    agent_breakdown: list[dict[str, Any]] = []
    for agent_id in STAGE_ORDER:
        agent_events = [e for e in events if e.get("agent_id") == agent_id]
        ok_n = sum(1 for e in agent_events if _event_status(e) == "ok")
        skipped_n = sum(1 for e in agent_events if _event_status(e) == "skipped")
        failed_n = sum(1 for e in agent_events if _event_status(e) == "failed")
        agent_breakdown.append({
            "Agent": agent_id,
            "OK": ok_n,
            "Skipped": skipped_n,
            "Failed": failed_n,
        })
    st.dataframe(agent_breakdown, use_container_width=True, hide_index=True)

    # Table: Record 1 .. Record 10, 8 stage columns with checkmarks
    st.subheader("Stage completion by record")
    rows = []
    for cid in ordered_cids:
        subset = _events_for_correlation(events, cid)
        agent_ids_present = {e.get("agent_id") for e in subset}
        row = {"record": cid_to_label.get(cid, cid)}
        for stage in STAGE_ORDER:
            row[stage] = "✓" if stage in agent_ids_present else ""
        rows.append(row)

    st.dataframe(
        [{"record": r["record"], **{s: r[s] for s in STAGE_ORDER}} for r in rows],
        column_config={"record": st.column_config.TextColumn("Record", width="medium")},
        use_container_width=True,
        hide_index=True,
    )


def render_page_journey(events: list[dict[str, Any]]) -> None:
    """Page 2: Record Journey — select by record label, show timeline and validation checkmarks."""
    st.title("Record Journey")

    if not events:
        st.warning("No pipeline run data found. Run the pipeline first to generate pipeline_run.json.")
        return

    ordered_cids, cid_to_label = _correlation_id_order(events)
    record_options = _record_dropdown_labels(events, ordered_cids)
    label_to_cid = {record_options[i]: ordered_cids[i] for i in range(len(ordered_cids))}

    selected_label = st.selectbox(
        "Select a record",
        options=record_options,
        key="journey_record_select",
    )
    selected_id = label_to_cid.get(selected_label) if selected_label else None

    if selected_id:
        st.caption("Correlation ID")
        st.code(selected_id, language=None)

    if not selected_id:
        return

    subset = _events_for_correlation(events, selected_id)
    if not subset:
        st.info("No events found for this record.")
        return

    # Table: Agent, Status, Timestamp, Schema Version, Payload Keys
    table_data = [
        {
            "Agent": e.get("agent_id", "—"),
            "Status": _event_status(e),
            "Timestamp": e.get("timestamp", "—"),
            "Schema Version": e.get("schema_version", "—"),
            "Payload Keys": _payload_keys_summary(e.get("payload") or {}),
        }
        for e in subset
    ]
    st.dataframe(table_data, use_container_width=True, hide_index=True)

    # Validation checkmarks at bottom
    st.subheader("Validation")
    correlation_ids_in_subset = [e.get("correlation_id") for e in subset]
    schema_versions = [e.get("schema_version") for e in subset]
    correlation_consistent = len(set(correlation_ids_in_subset)) == 1 and all(
        c == selected_id for c in correlation_ids_in_subset
    )
    schema_ok = all(sv == "1.0" for sv in schema_versions)

    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Correlation ID consistent across all steps", value=correlation_consistent, disabled=True)
    with col2:
        st.checkbox("Schema version 1.0 for all steps", value=schema_ok, disabled=True)


def render_page_insights(events: list[dict[str, Any]]) -> None:
    """Page 3: Batch Insights — top skills, seniority distribution, companies/locations from payloads."""
    st.title("Batch Insights")

    if not events:
        st.warning("No pipeline run data found. Run the pipeline first to generate pipeline_run.json.")
        return

    # Use first analytics event payload for top_skills and seniority_distribution.
    analytics_events = [e for e in events if e.get("agent_id") == "analytics"]
    analytics_payload = (analytics_events[0].get("payload") or {}) if analytics_events else {}

    # Top skills bar chart (from analytics fixture payload)
    top_skills = analytics_payload.get("top_skills") or []
    if top_skills:
        st.subheader("Top skills (from analytics payload)")
        # Each item: {"skill": str, "count": int, "type": str}
        skills_labels = [s.get("skill", "?") for s in top_skills]
        skills_counts = [s.get("count", 0) for s in top_skills]
        st.bar_chart(dict(zip(skills_labels, skills_counts)))
    else:
        st.info("No top_skills data in analytics payload.")

    # Seniority distribution bar chart
    seniority_dist = analytics_payload.get("seniority_distribution") or {}
    if seniority_dist:
        st.subheader("Seniority distribution")
        st.bar_chart(seniority_dist)
    else:
        st.info("No seniority_distribution data in analytics payload.")

    # Companies and locations table — from ingestion payload (sample_raw_record) or enrichment.
    # Prefer first ingestion event's sample_raw_record (has company + location).
    ingestion_events = [e for e in events if e.get("agent_id") == "ingestion"]
    companies_locations: list[dict[str, str]] = []
    if ingestion_events:
        payload = ingestion_events[0].get("payload") or {}
        raw_records = payload.get("sample_raw_record")
        if isinstance(raw_records, list):
            for r in raw_records:
                if isinstance(r, dict):
                    companies_locations.append({
                        "company": r.get("company", "—"),
                        "location": r.get("location", "—"),
                    })
    # Fallback: enrichment payload enriched_records (company only; no location in fixture).
    if not companies_locations:
        enrichment_events = [e for e in events if e.get("agent_id") == "enrichment"]
        if enrichment_events:
            payload = enrichment_events[0].get("payload") or {}
            enriched = payload.get("enriched_records", []) if isinstance(payload, dict) else []
            if isinstance(enriched, list):
                for r in enriched:
                    if isinstance(r, dict):
                        companies_locations.append({
                            "company": r.get("company", "—"),
                            "location": r.get("location", "—"),
                        })

    st.subheader("Companies and locations")
    if companies_locations:
        st.dataframe(companies_locations, use_container_width=True, hide_index=True)
    else:
        st.info("No companies/locations data found in pipeline payloads.")


def main() -> None:
    """Load data, sidebar navigation, and render selected page."""
    events = load_pipeline_run()

    st.sidebar.title("Pipeline Dashboard")
    st.sidebar.caption("Job Intelligence Engine")

    _inject_theme_css("Dark")

    page = st.sidebar.radio(
        "Navigate",
        options=["Summary", "Record Journey", "Batch Insights"],
        key="main_nav",
        label_visibility="collapsed",
    )

    if page == "Summary":
        render_page_summary(events)
    elif page == "Record Journey":
        render_page_journey(events)
    else:
        render_page_insights(events)


def _inject_theme_css(theme: str) -> None:
    """Inject CSS for light/dark mode and nicer table styling."""
    if theme == "Dark":
        bg = "#0f172a"
        surface = "#1e293b"
        card = "#334155"
        text = "#f1f5f9"
        text_muted = "#94a3b8"
        border = "#475569"
    else:
        bg = "#f8fafc"
        surface = "#ffffff"
        card = "#e0e7ff"
        text = "#1e293b"
        text_muted = "#64748b"
        border = "#cbd5e1"

    st.markdown(
        f"""
    <style>
    [data-testid="stAppViewContainer"] {{ background-color: {bg}; }}
    [data-testid="stHeader"] {{ background-color: {surface}; }}
    [data-testid="stSidebar"] > div {{ background-color: {surface}; }}
    [data-testid="stSidebar"] .stMarkdown {{ color: {text}; }}
    [data-testid="stMetricValue"], .stMarkdown {{ color: {text} !important; }}
    [data-testid="stMetricLabel"] {{ color: {text_muted} !important; }}
    .stDataFrame {{
        background-color: {card} !important;
        border-radius: 8px;
        border: 1px solid {border};
        overflow: hidden;
    }}
    .stDataFrame div[data-testid="stDataFrameResizable"] {{ background-color: {card} !important; }}
    .stDataFrame thead tr th {{
        background-color: {border} !important;
        color: {text} !important;
        font-weight: 600;
        padding: 0.5rem 0.75rem;
    }}
    .stDataFrame tbody tr td {{
        background-color: {card} !important;
        color: {text} !important;
        padding: 0.5rem 0.75rem;
    }}
    .stDataFrame tbody tr:hover td {{ background-color: {surface} !important; }}
    </style>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
