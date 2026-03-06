"""
Streamlit dashboard for Job Intelligence Engine (Exercise 1.3 + Task 2.5).

- Scraped postings: loads raw_scrape_sample.json (Exercise 1.2), expandable cards, filter by source.
- Pipeline Run Summary / Record Journey / Batch Insights: use pipeline_run.json (Task 2.5).

Run from repo root: streamlit run agents/dashboard/streamlit_app.py
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# Ensure repo root is on path so "from agents.common ..." works when run via streamlit run
_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]  # agents/dashboard -> agents -> repo root
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd
import streamlit as st

from agents.common.datetime_utils import format_iso_timestamp_for_display
from agents.common.paths import PIPELINE_RUN_JSON, RAW_SCRAPE_SAMPLE_PATH as _JSON_PATH

# Page identifiers
PAGE_PIPELINE_SUMMARY = "Pipeline Run Summary"
PAGE_RECORD_JOURNEY = "Record Journey"
PAGE_BATCH_INSIGHTS = "Batch Insights"
PAGE_SCRAPED_POSTINGS = "Scraped postings"

# Debug only: include a source option with no postings to test list depopulation.
DEBUG_SIDEBAR = os.getenv("STREAMLIT_DEBUG_SIDEBAR", "").lower() in ("1", "true")
TEST_SOURCE_NO_DATA = "jsearch"

# Agent ID -> display event name for Page 2
AGENT_EVENT_NAMES = {
    "ingestion_agent": "IngestBatch",
    "normalization_agent": "NormalizationComplete",
    "skills_extraction_agent": "SkillsExtracted",
    "enrichment_agent": "RecordEnriched",
    "demand_analysis_agent": "DemandSignalsUpdated / Phase 2 skipped",
    "analytics_agent": "AnalyticsRefreshed",
    "visualization_agent": "RenderComplete",
    "orchestration_agent": "Orchestration",
}


@st.cache_data(ttl=60)
def _load_pipeline_run() -> dict | None:
    """Load pipeline_run.json. Return None if missing or invalid."""
    if not PIPELINE_RUN_JSON.exists():
        return None
    try:
        raw = PIPELINE_RUN_JSON.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or "events" not in data:
        return None
    return data


def _compute_duration_seconds(run: dict) -> float | None:
    """Parse started_at and finished_at; return duration in seconds or None."""
    started = run.get("started_at")
    finished = run.get("finished_at")
    if not started or not finished:
        return None
    try:
        start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(finished.replace("Z", "+00:00"))
        return (end_dt - start_dt).total_seconds()
    except (ValueError, TypeError):
        return None


def _load_postings() -> list[dict]:
    """Load postings from raw_scrape_sample.json. Return [] on missing or invalid file."""
    if not _JSON_PATH.exists():
        return []
    try:
        with open(_JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return data


def _safe_get(record: dict, key: str, default: str = "") -> str:
    """Return record[key] or default; coerce to str for display."""
    val = record.get(key, default)
    if val is None:
        return default
    return str(val)


def _source_for_filter(record: dict) -> str:
    """Normalized source value for sidebar options and filter (empty/missing → 'Unknown')."""
    return _safe_get(record, "source", "").strip() or "Unknown"


def _render_pipeline_run_summary(run: dict) -> None:
    """Page 1: Run metadata, all-records-through-all-stages, correlation ID table."""
    st.title("Pipeline Run Summary")

    run_id = run.get("run_id", "—")
    started_at = run.get("started_at", "")
    finished_at = run.get("finished_at", "")
    input_count = run.get("input_record_count", 0)
    events = run.get("events") or []

    st.markdown("**Run ID**  \n`" + str(run_id) + "`")
    st.markdown("**Started**  \n" + format_iso_timestamp_for_display(started_at))
    st.markdown("**Finished**  \n" + format_iso_timestamp_for_display(finished_at))
    duration_sec = _compute_duration_seconds(run)
    if duration_sec is not None:
        st.markdown("**Duration**  \n" + f"{duration_sec:.3f} s")
    st.markdown("**Input records**  \n" + str(input_count))

    # Did all 10 records make it through all 8 stages?
    cid_counts = Counter(ev.get("correlation_id") for ev in events if isinstance(ev, dict))
    unique_cids = len(cid_counts)
    expected_stages = 8
    all_ok = unique_cids == input_count and all(c == expected_stages for c in cid_counts.values())

    st.subheader("Did all records make it through all 8 stages?")
    if all_ok:
        st.success("Yes. All " + str(input_count) + " records completed all 8 stages.")
    else:
        bad = [(cid, c) for cid, c in cid_counts.items() if c != expected_stages]
        if bad:
            st.warning("No. Some records have a different stage count: " + str(bad[:5]))
        if unique_cids != input_count:
            st.warning("Unique correlation_ids: " + str(unique_cids) + ", expected " + str(input_count))

    # Correlation ID table
    st.subheader("Correlation ID table")
    rows = []
    for cid, count in sorted(cid_counts.items(), key=lambda x: (x[1], x[0])):
        status = "OK" if count == expected_stages else "Partial"
        rows.append({"Correlation ID": cid, "Stages completed": f"{count}/{expected_stages}", "Status": status})
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No events in this run.")


def _render_record_journey(run: dict) -> None:
    """Page 2: Dropdown by correlation_id, timeline for selected record only."""
    st.title("Record Journey")

    events = run.get("events") or []
    cid_counts = Counter(ev.get("correlation_id") for ev in events if isinstance(ev, dict))
    unique_cids = list(cid_counts.keys())
    if not unique_cids:
        st.info("No records in this run.")
        return

    # Preserve order of first occurrence for "Record 1", "Record 2", ...
    order = {}
    for ev in events:
        cid = ev.get("correlation_id") if isinstance(ev, dict) else None
        if cid and cid not in order:
            order[cid] = len(order) + 1
    options = sorted(unique_cids, key=lambda c: order.get(c, 999))
    labels = [f"Record {order.get(c, i)} — {c[:8]}…" for i, c in enumerate(options, start=1)]
    choice_map = dict(zip(labels, options))

    selected_label = st.selectbox("Select record", options=labels, key="record_journey_select")
    selected_cid = choice_map.get(selected_label, options[0] if options else "")

    st.caption("**Correlation ID:** `" + selected_cid + "`")

    # Filter: only events for this correlation_id (single source of truth for timeline)
    filtered_events = [ev for ev in events if isinstance(ev, dict) and ev.get("correlation_id") == selected_cid]

    if not filtered_events:
        st.info("No events for this record.")
        return

    for i, ev in enumerate(filtered_events, start=1):
        agent_id = ev.get("agent_id", "—")
        ts = ev.get("timestamp", "")
        payload = ev.get("payload") or {}
        event_name = AGENT_EVENT_NAMES.get(agent_id, agent_id)
        if agent_id == "demand_analysis_agent" and payload.get("phase2_skipped"):
            event_name = "Phase 2 skipped"

        with st.expander(f"Stage {i}: {agent_id}", expanded=(i <= 2)):
            st.markdown("**Event**  \n" + event_name)
            st.markdown("**Timestamp**  \n" + format_iso_timestamp_for_display(ts))
            summary_parts = []
            if "record_count" in payload:
                summary_parts.append("record_count=" + str(payload["record_count"]))
            if "batch_id" in payload:
                summary_parts.append("batch_id=" + str(payload["batch_id"])[:20] + "…")
            if "phase2_skipped" in payload:
                summary_parts.append("phase2_skipped=" + str(payload["phase2_skipped"]))
            st.markdown("**Payload summary**  \n" + (", ".join(summary_parts) or "(no summary keys)"))
            with st.expander("Raw payload (optional)"):
                st.json(payload)


def _render_batch_insights(run: dict) -> None:
    """Page 3: Skills bar chart, seniority chart, companies and locations — all from event payloads."""
    st.title("Batch Insights")

    events = run.get("events") or []

    # Skills/seniority: from skills_extraction_agent payload.records.
    # Current stub: every event has the full fixture (10 records), so use first event only to avoid 10x duplication.
    # When Skills Extraction is real: each event will have 1 record; then aggregate all skills_extraction_agent events.
    skills_events = [ev for ev in events if isinstance(ev, dict) and ev.get("agent_id") == "skills_extraction_agent"]
    records_for_insights = []
    if skills_events:
        payload = skills_events[0].get("payload") or {}
        records_for_insights = payload.get("records") or []

    # Seniority fallback: from enrichment_agent (same contract — stub has full fixture per event)
    enrichment_events = [ev for ev in events if isinstance(ev, dict) and ev.get("agent_id") == "enrichment_agent"]
    if enrichment_events and not records_for_insights:
        payload = enrichment_events[0].get("payload") or {}
        records_for_insights = payload.get("records") or []

    # Companies/locations: from ingestion_agent events (one record per event)
    ingestion_events = [ev for ev in events if isinstance(ev, dict) and ev.get("agent_id") == "ingestion_agent"]
    companies_locations = []
    for ev in ingestion_events:
        payload = ev.get("payload") or {}
        recs = payload.get("records") or []
        if recs:
            r = recs[0]
            companies_locations.append((r.get("company") or "—", r.get("location") or "—"))

    if not records_for_insights and not companies_locations:
        st.info("No batch insight data in this run.")
        return

    # Skills bar chart — real data from payload.records[].skills
    if records_for_insights:
        skill_counts: Counter = Counter()
        for rec in records_for_insights:
            for s in rec.get("skills") or []:
                name = s.get("name") if isinstance(s, dict) else str(s)
                if name:
                    skill_counts[name] += 1
        if skill_counts:
            st.subheader("Top skills across postings")
            top_n = 15
            sorted_skills = skill_counts.most_common(top_n)
            chart_df = pd.DataFrame(sorted_skills, columns=["Skill", "Count"])
            st.bar_chart(chart_df, x="Skill", y="Count", height=400)

        # Seniority — real data from payload.records[].seniority
        st.subheader("Seniority distribution")
        seniority_counts: Counter = Counter()
        for rec in records_for_insights:
            s = rec.get("seniority")
            if s:
                seniority_counts[str(s)] += 1
        if seniority_counts:
            sr_df = pd.DataFrame(
                [{"Seniority": k, "Count": v} for k, v in seniority_counts.most_common()]
            )
            st.bar_chart(sr_df, x="Seniority", y="Count", height=300)
        else:
            st.caption("No seniority data in payloads.")
    else:
        st.caption("No skills/seniority data in this run.")

    # Companies and locations represented
    st.subheader("Companies and locations represented")
    if companies_locations:
        cl_df = pd.DataFrame(companies_locations, columns=["Company", "Location"])
        st.dataframe(cl_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No company/location data in ingestion payloads.")


def _render_scraped_postings() -> None:
    """Original Scraped postings page (Exercise 1.3)."""
    st.title("Scraped job postings")
    postings = _load_postings()

    if not postings:
        st.info("No data. Run the scraper first (Exercise 1.2) to generate raw_scrape_sample.json.")
        return

    sources = sorted({_source_for_filter(p) for p in postings})
    source_options = ["All"] + sources + ([TEST_SOURCE_NO_DATA] if DEBUG_SIDEBAR else [])
    selected_source = st.sidebar.selectbox(
        "Filter by source",
        options=source_options,
        index=0,
        key="scraped_filter",
    )

    if selected_source == "All":
        filtered = postings
    else:
        filtered = [p for p in postings if _source_for_filter(p) == selected_source]

    st.caption(f"Showing {len(filtered)} of {len(postings)} posting(s)")

    if not filtered:
        st.warning("No postings for the selected source: **" + TEST_SOURCE_NO_DATA + "**. Try another source.")
    else:
        for i, record in enumerate(filtered, start=1):
            source = _source_for_filter(record)
            url = _safe_get(record, "url", "—")
            timestamp_raw = _safe_get(record, "timestamp", "—")
            timestamp_display = format_iso_timestamp_for_display(timestamp_raw)
            raw_text = _safe_get(record, "raw_text", "")

            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                label = parsed.netloc or (url[:50] + "…" if len(url) > 50 else url) if url else f"Posting {i}"
            except Exception:
                label = f"Posting {i}"

            with st.expander(f"{label} — {source}", expanded=False):
                st.markdown("**Source**  \n" + source)
                if url and url != "—":
                    st.markdown("**URL**  \n" + f"[{url}]({url})")
                else:
                    st.markdown("**URL**  \n—")
                st.markdown("**Scraped**  \n" + timestamp_display)
                st.markdown("---")
                st.markdown("**Content**")
                if raw_text:
                    st.text_area(
                        "Raw text",
                        value=raw_text,
                        height=min(400, max(120, 50 + raw_text.count("\n") * 18)),
                        key=f"raw_text_{i}",
                        disabled=True,
                        label_visibility="collapsed",
                    )
                else:
                    st.caption("(no text)")


# --- Main: page config and routing ---
st.set_page_config(page_title="Job Intelligence Engine", layout="wide")

page_options = [PAGE_PIPELINE_SUMMARY, PAGE_RECORD_JOURNEY, PAGE_BATCH_INSIGHTS, PAGE_SCRAPED_POSTINGS]
selected_page = st.sidebar.radio(
    "Page",
    options=page_options,
    index=0,
    label_visibility="collapsed",
)

if selected_page == PAGE_SCRAPED_POSTINGS:
    _render_scraped_postings()
else:
    run = _load_pipeline_run()
    if run is None:
        st.info("Run the pipeline first to generate pipeline_run.json (e.g. `python -m agents.pipeline_runner`).")
        st.stop()
    if selected_page == PAGE_PIPELINE_SUMMARY:
        _render_pipeline_run_summary(run)
    elif selected_page == PAGE_RECORD_JOURNEY:
        _render_record_journey(run)
    elif selected_page == PAGE_BATCH_INSIGHTS:
        _render_batch_insights(run)
