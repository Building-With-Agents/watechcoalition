# agents/dashboard/streamlit_app.py
"""Streamlit dashboard — Phase 1. Run: streamlit run agents/dashboard/streamlit_app.py"""

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

# Eight pipeline stages (agents) in order
PIPELINE_STAGES = [
    "ingestion_agent",
    "normalization_agent",
    "skills_extraction_agent",
    "enrichment_agent",
    "analytics_agent",
    "visualization_agent",
    "orchestration_agent",
    "demand_analysis_agent",
]

# Default path from Exercise 1.2 (scraper_adapter writes to agents/data/staging/raw_scrape_sample.json)
def _default_raw_scrape_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "staging" / "raw_scrape_sample.json"


def _default_pipeline_run_path() -> Path:
    """Default path for pipeline run log (pipeline_runner writes to agents/data/output/pipeline_run.json)."""
    return Path(__file__).resolve().parents[1] / "data" / "output" / "pipeline_run.json"


@st.cache_data(ttl=60)
def _load_pipeline_run(path: str) -> dict | None:
    """Load pipeline run JSON. Returns None on missing file or invalid JSON."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return None
    if not isinstance(data, dict) or "events" not in data:
        return None
    return data


def _load_raw_scrape(path: Path) -> list[dict] | None:
    """Load list of raw job postings from JSON. Returns None on missing file or invalid JSON."""
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return None
    if not isinstance(data, list):
        return None
    return data


def _source_identifier(record: dict) -> str:
    """Derive a short source name from the record (e.g. hostname from source_url)."""
    url = record.get("source_url") or record.get("url") or ""
    if not url:
        return "Unknown"
    parsed = urlparse(url)
    netloc = (parsed.netloc or "").strip()
    if netloc:
        return netloc
    return url[:50] + ("..." if len(url) > 50 else "")


def _raw_text_preview(record: dict, max_chars: int = 280) -> str:
    """First ~200–300 chars of description or title+description for preview."""
    desc = record.get("description") or ""
    if desc:
        text = desc.strip()
    else:
        text = (record.get("title") or "").strip()
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def _timestamp_str(record: dict) -> str | None:
    """Return a timestamp string if present (e.g. date_posted or scraped_at)."""
    for key in ("scraped_at", "ingestion_timestamp", "date_posted", "timestamp"):
        val = record.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


st.set_page_config(page_title="Job Intelligence Engine", layout="wide")

# --- Sidebar: page selector ---
PAGE_RAW_SCRAPE = "Raw Scrape Viewer"
PAGE_PIPELINE_SUMMARY = "Pipeline Run Summary"
PAGE_RECORD_JOURNEY = "Record Journey"
PAGE_BATCH_INSIGHTS = "Batch Insights"

st.sidebar.markdown("**Page**")
page = st.sidebar.radio(
    "Select page",
    [PAGE_RAW_SCRAPE, PAGE_PIPELINE_SUMMARY, PAGE_RECORD_JOURNEY, PAGE_BATCH_INSIGHTS],
    label_visibility="collapsed",
)

# --- Pipeline run path (for the three pipeline pages) ---
pipeline_run_path_str = ""
if page in (PAGE_PIPELINE_SUMMARY, PAGE_RECORD_JOURNEY, PAGE_BATCH_INSIGHTS):
    default_pipeline_path = _default_pipeline_run_path()
    custom_pipeline_str = st.sidebar.text_input(
        "Pipeline run JSON path (optional)",
        value="",
        help=f"Leave empty to use default: {default_pipeline_path}",
        key="pipeline_run_path",
    )
    pipeline_run_path_str = custom_pipeline_str.strip() or str(default_pipeline_path)

st.title("Job Intelligence Engine — Dashboard")

if page == PAGE_RAW_SCRAPE:
    st.caption(
        "Phase 1. Raw Scrape Viewer (Exercise 1.2) | "
        "Pages: Ingestion Overview | Normalization Quality | Skill Taxonomy | Weekly Insights | Ask the Data | Operations & Alerts."
    )
    # --- Raw Scrape Viewer ---
    st.subheader("Raw Scrape Viewer")
    default_path = _default_raw_scrape_path()
    custom_path_str = st.sidebar.text_input(
        "JSON path (optional)",
        value="",
        help=f"Leave empty to use default: {default_path}",
        key="raw_scrape_path",
    )
    data_path = Path(custom_path_str.strip()) if custom_path_str.strip() else default_path
    postings = _load_raw_scrape(data_path)
    if postings is None:
        if not data_path.exists():
            st.warning(f"File not found: `{data_path}`. Run the scraper (e.g. `python -m agents.ingestion.sources.scraper_adapter`) to generate it.")
        else:
            st.error(f"Could not load valid JSON from `{data_path}` (expected a list of job objects).")
        st.stop()
    sources = sorted({_source_identifier(r) for r in postings})
    st.sidebar.markdown("**Filter by source**")
    show_all = st.sidebar.checkbox("All sources", value=True, key="show_all_sources")
    if show_all:
        selected_sources = sources
    else:
        selected_sources = st.sidebar.multiselect(
            "Sources",
            options=sources,
            default=sources[:1] if sources else [],
            key="source_filter",
        )
    filtered = [p for p in postings if _source_identifier(p) in selected_sources]
    st.sidebar.caption(f"Showing {len(filtered)} of {len(postings)} postings")
    PREVIEW_CHARS = 280
    for i, record in enumerate(filtered):
        source = _source_identifier(record)
        url_scraped = record.get("source_url") or record.get("url") or ""
        timestamp = _timestamp_str(record)
        preview = _raw_text_preview(record, max_chars=PREVIEW_CHARS)
        title_display = (record.get("title") or "Untitled").strip() or "Untitled"
        label = f"**{title_display[:60]}{'…' if len(title_display) > 60 else ''}** — {source}"
        with st.expander(label, expanded=False):
            st.markdown(f"**Source:** `{source}`")
            if url_scraped:
                st.markdown(f"**URL scraped:** [{url_scraped}]({url_scraped})")
            if timestamp:
                st.markdown(f"**Timestamp:** {timestamp}")
            st.markdown("**Raw text preview:**")
            st.text(preview if preview else "(no description or title)")
            st.markdown("---")
            st.markdown("**Full raw text:**")
            full_text = (record.get("description") or "").strip() or (record.get("title") or "").strip()
            st.text(full_text if full_text else "(empty)")
            with st.expander("View full record (JSON)", expanded=False):
                st.json(record)

else:
    # --- Load pipeline run for Summary / Record Journey / Batch Insights ---
    run_data = _load_pipeline_run(pipeline_run_path_str) if pipeline_run_path_str else None
    if run_data is None:
        st.warning(
            f"Pipeline run file not found or invalid: `{pipeline_run_path_str}`. "
            "Run the pipeline (e.g. `python -m agents.pipeline_runner`) to generate it."
        )
        st.stop()

    events = run_data.get("events") or []
    run_at = run_data.get("run_at")
    records_processed = run_data.get("records_processed", 0)
    total_events = run_data.get("total_events", 0)

    # Group events by correlation_id; each entry is either full event (has agent_id) or failure (has stage)
    def _agent_from_entry(entry: dict) -> str | None:
        if "agent_id" in entry:
            return entry["agent_id"]
        return entry.get("stage")

    by_correlation: dict[str, list[dict]] = {}
    for ev in events:
        cid = ev.get("correlation_id")
        if not cid:
            continue
        if cid not in by_correlation:
            by_correlation[cid] = []
        by_correlation[cid].append(ev)

    correlation_ids = list(by_correlation.keys())

    def _stages_completed(entries: list[dict]) -> dict[str, str]:
        """For a list of entries (one record), return stage -> status: OK, Skipped, Error."""
        seen: dict[str, str] = {}
        for e in entries:
            agent = _agent_from_entry(e)
            if not agent:
                continue
            if "event" in e and e.get("event") is None:
                reason = e.get("reason") or e.get("error") or "failed"
                seen[agent] = "Error" if "error" in e else "Skipped"
            else:
                seen[agent] = "OK"
        return {s: seen.get(s, "—") for s in PIPELINE_STAGES}

    # --- Page 1: Pipeline Run Summary ---
    if page == PAGE_PIPELINE_SUMMARY:
        st.subheader("Pipeline Run Summary")
        # Did all N records make it through all 8 stages? (has an entry for every stage)
        expected_count = records_processed
        completed_all = sum(
            1 for _cid, entries in by_correlation.items()
            if all(_stages_completed(entries).get(s) != "—" for s in PIPELINE_STAGES)
        )
        if expected_count > 0 and completed_all == expected_count:
            st.success(f"Yes, all {expected_count} records completed all 8 stages.")
        else:
            st.warning(
                f"No: {completed_all} of {expected_count} records completed all 8 stages."
                + (f" Incomplete: {expected_count - completed_all}." if expected_count > completed_all else "")
            )
        # When did the run happen and how long did it take?
        st.markdown("**Run time**")
        if run_at:
            try:
                dt = datetime.fromisoformat(run_at.replace("Z", "+00:00"))
                st.text(f"Started: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            except (ValueError, TypeError):
                st.text(f"Started: {run_at}")
        else:
            st.text("Started: N/A")
        timestamps = [
            e.get("timestamp") for e in events
            if isinstance(e.get("timestamp"), str)
        ]
        if timestamps:
            try:
                t_min = min(datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in timestamps)
                t_max = max(datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in timestamps)
                duration = (t_max - t_min).total_seconds()
                st.text(f"Duration: {duration:.2f} s")
            except (ValueError, TypeError):
                st.text("Duration: N/A")
        else:
            st.text("Duration: N/A")
        # Filter by correlation_id, then show 8 stages for selected record(s)
        st.markdown("**Correlation ID — stage completion**")
        filter_options = ["All records"] + correlation_ids
        filter_choice = st.selectbox(
            "Filter by correlation_id",
            range(len(filter_options)),
            format_func=lambda i: filter_options[i] if i == 0 else f"{filter_options[i][:8]}… ({filter_options[i]})",
            key="pipeline_summary_cid_filter",
        )
        cids_to_show = correlation_ids if filter_choice == 0 else [filter_options[filter_choice]]
        rows = []
        for cid in cids_to_show:
            entries = by_correlation[cid]
            statuses = _stages_completed(entries)
            row = {"correlation_id": cid}
            for s in PIPELINE_STAGES:
                row[s] = statuses.get(s, "—")
            rows.append(row)
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # --- Page 2: Record Journey ---
    elif page == PAGE_RECORD_JOURNEY:
        st.subheader("Record Journey")
        # Build labels for dropdown: correlation_id with optional title/company from first IngestBatch
        options = []
        for cid in correlation_ids:
            entries = by_correlation[cid]
            label = cid
            for e in entries:
                if e.get("agent_id") == "ingestion_agent":
                    p = e.get("payload") or {}
                    if p.get("event_type") == "IngestBatch":
                        title = (p.get("title") or "").strip() or "Untitled"
                        company = (p.get("company") or "").strip()
                        if company:
                            label = f"{cid[:8]}… — {title[:40]} @ {company}"
                        else:
                            label = f"{cid[:8]}… — {title[:50]}"
                        break
            options.append(label)
        choice_idx = st.selectbox(
            "Select record by correlation_id",
            range(len(correlation_ids)),
            format_func=lambda i: options[i],
            key="record_journey_select",
        )
        selected_cid = correlation_ids[choice_idx]
        st.code(selected_cid, language=None)
        entries = by_correlation[selected_cid]
        st.markdown("**Timeline**")
        timeline_data = []
        for e in entries:
            agent = _agent_from_entry(e) or "—"
            if "payload" in e and isinstance(e["payload"], dict):
                event_name = e["payload"].get("event_type") or "—"
                # Payload summary: for IngestBatch show title, company, location
                p = e["payload"]
                if event_name == "IngestBatch":
                    summary = f"title={p.get('title', '')[:40]}… | company={p.get('company')} | location={p.get('location')}"
                else:
                    keys = list(p.keys())[:6]
                    summary = ", ".join(keys) + ("…" if len(p) > 6 else "")
            else:
                event_name = e.get("reason") or e.get("error") or "N/A"
                summary = event_name
            ts = e.get("timestamp")
            timeline_data.append({
                "Agent": agent,
                "Event": event_name,
                "Timestamp": ts if ts else "—",
                "Payload summary": summary[:80] + ("…" if len(summary) > 80 else ""),
            })
        st.dataframe(pd.DataFrame(timeline_data), use_container_width=True, hide_index=True)

    # --- Page 3: Batch Insights ---
    else:
        st.subheader("Batch Insights")
        # Top skills: from first AnalyticsRefreshed, else from SkillsExtracted
        top_skills: list[dict] = []
        for e in events:
            p = e.get("payload") or {}
            if p.get("event_type") == "AnalyticsRefreshed" and "top_skills" in p:
                top_skills = p["top_skills"]
                break
        if not top_skills:
            for e in events:
                p = e.get("payload") or {}
                if p.get("event_type") == "SkillsExtracted" and "records" in p:
                    skill_counts: dict[str, int] = {}
                    for rec in p.get("records") or []:
                        for sk in rec.get("skills") or []:
                            name = sk.get("name") or sk.get("label") or ""
                            if name:
                                skill_counts[name] = skill_counts.get(name, 0) + 1
                    top_skills = [{"skill": k, "count": v} for k, v in sorted(skill_counts.items(), key=lambda x: -x[1])]
                    break
        if top_skills:
            st.markdown("**Top skills across postings**")
            df_skills = pd.DataFrame(top_skills)
            if "skill" in df_skills.columns and "count" in df_skills.columns:
                st.bar_chart(df_skills.set_index("skill")["count"])
            else:
                st.dataframe(df_skills, use_container_width=True, hide_index=True)
        else:
            st.info("No skills data in run.")
        # Seniority distribution
        seniority_counts: dict[str, int] = {}
        for e in events:
            p = e.get("payload") or {}
            if p.get("event_type") == "RecordEnriched" and "records" in p:
                for rec in p.get("records") or []:
                    s = (rec.get("seniority") or "unknown").strip() or "unknown"
                    seniority_counts[s] = seniority_counts.get(s, 0) + 1
                break
        if seniority_counts:
            st.markdown("**Seniority distribution**")
            df_sen = pd.DataFrame([
                {"seniority": k, "count": v} for k, v in seniority_counts.items()
            ])
            st.bar_chart(df_sen.set_index("seniority")["count"])
        else:
            st.info("No seniority data in run.")
        # Companies and locations
        companies_locations: list[dict] = []
        for cid in correlation_ids:
            for e in by_correlation[cid]:
                if e.get("agent_id") == "ingestion_agent":
                    p = e.get("payload") or {}
                    if p.get("event_type") == "IngestBatch":
                        companies_locations.append({
                            "company": p.get("company") or "—",
                            "location": p.get("location") or "—",
                        })
                        break
        if companies_locations:
            st.markdown("**Companies and locations**")
            st.dataframe(pd.DataFrame(companies_locations), use_container_width=True, hide_index=True)
        else:
            st.info("No company/location data in run.")
