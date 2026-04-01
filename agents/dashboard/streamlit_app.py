"""
Journey Dashboard — Database-connected Streamlit dashboard.

Three-page Streamlit dashboard for observing pipeline data.

Pages
-----
1. Pipeline Run Summary   — ingestion runs, record counts, stage completion.
2. Record Journey         — select one record and trace it through stages.
3. Batch Insights         — aggregate charts: locations, employment types,
                            experience levels, salary distributions, sources.

Data source: PostgreSQL (via SQLAlchemy) with JSON file fallback.

Usage:
    streamlit run agents/dashboard/streamlit_app.py
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment & paths
# ---------------------------------------------------------------------------

load_dotenv()

_HERE = Path(__file__).parent.parent  # agents/
_RUN_LOG_PATH = _HERE / "data" / "output" / "pipeline_run.json"

_AGENT_ORDER = [
    "ingestion-agent",
    "normalization-agent",
    "skills-extraction-agent",
    "enrichment-agent",
    "analytics-agent",
    "visualization-agent",
    "orchestration-agent",
    "demand-analysis-agent",
]
_AGENT_ORDER_INDEX = {a: i for i, a in enumerate(_AGENT_ORDER)}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _db_available() -> bool:
    """Check if PostgreSQL is reachable."""
    if not os.getenv("PYTHON_DATABASE_URL"):
        return False
    try:
        from agents.common.data_store import check_db_connection

        return check_db_connection()
    except Exception:
        return False


@st.cache_data(ttl=60)
def _load_ingestion_runs() -> pd.DataFrame:
    """Load ingestion run history from DB."""
    from agents.common.data_store import get_engine

    query = """
        SELECT run_id, region_id, source, started_at, completed_at,
               status, total_fetched, staged_count, dedup_count, error_count,
               error_message
        FROM dbo.job_ingestion_runs
        ORDER BY started_at DESC
        LIMIT 50
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=60)
def _load_raw_jobs(run_id: str | None = None) -> pd.DataFrame:
    """Load raw ingested jobs, optionally filtered by run_id."""
    from agents.common.data_store import get_engine

    if run_id:
        query = """
            SELECT id, ingestion_run_id, region_id, source, external_id,
                   title, company, city, state, country, is_remote,
                   date_posted, employment_type, experience_level,
                   salary_min, salary_max, salary_currency, salary_period,
                   processing_status, error_message, ingestion_timestamp
            FROM dbo.raw_ingested_jobs
            WHERE ingestion_run_id = %(run_id)s
            ORDER BY id
        """
        return pd.read_sql(query, get_engine(), params={"run_id": run_id})
    query = """
        SELECT id, ingestion_run_id, region_id, source, external_id,
               title, company, city, state, country, is_remote,
               date_posted, employment_type, experience_level,
               salary_min, salary_max, salary_currency, salary_period,
               processing_status, error_message, ingestion_timestamp
        FROM dbo.raw_ingested_jobs
        ORDER BY id DESC
        LIMIT 500
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=60)
def _load_normalized_jobs(run_id: str | None = None) -> pd.DataFrame:
    """Load normalized jobs, optionally filtered by run_id."""
    from agents.common.data_store import get_engine

    if run_id:
        query = """
            SELECT id, raw_job_id, ingestion_run_id, region_id, source, external_id,
                   title, company, city, state_province, country,
                   work_arrangement, is_remote, employment_type, experience_level,
                   date_posted, salary_min, salary_max, salary_currency, salary_period,
                   normalization_status, created_at
            FROM dbo.normalized_jobs
            WHERE ingestion_run_id = %(run_id)s
            ORDER BY id
        """
        return pd.read_sql(query, get_engine(), params={"run_id": run_id})
    query = """
        SELECT id, raw_job_id, ingestion_run_id, region_id, source, external_id,
               title, company, city, state_province, country,
               work_arrangement, is_remote, employment_type, experience_level,
               date_posted, salary_min, salary_max, salary_currency, salary_period,
               normalization_status, created_at
        FROM dbo.normalized_jobs
        ORDER BY id DESC
        LIMIT 500
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=60)
def _load_quarantined(run_id: str | None = None) -> pd.DataFrame:
    """Load quarantined records."""
    from agents.common.data_store import get_engine

    if run_id:
        query = """
            SELECT id, raw_job_id, ingestion_run_id, source, external_id,
                   error_type, error_detail, quarantined_at
            FROM dbo.normalization_quarantine
            WHERE ingestion_run_id = %(run_id)s
            ORDER BY quarantined_at DESC
        """
        return pd.read_sql(query, get_engine(), params={"run_id": run_id})
    query = """
        SELECT id, raw_job_id, ingestion_run_id, source, external_id,
               error_type, error_detail, quarantined_at
        FROM dbo.normalization_quarantine
        ORDER BY quarantined_at DESC
        LIMIT 100
    """
    return pd.read_sql(query, get_engine())


# ---------------------------------------------------------------------------
# JSON fallback helpers (Week 2 walking skeleton compatibility)
# ---------------------------------------------------------------------------


@st.cache_data
def _load_run_log() -> list[dict]:
    """Load pipeline_run.json. Returns empty list if not found."""
    if not _RUN_LOG_PATH.exists():
        return []
    return json.loads(_RUN_LOG_PATH.read_text(encoding="utf-8"))


def _build_record_map(entries: list[dict]) -> dict[str, list[dict]]:
    record_map: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        cid = entry.get("correlation_id", "unknown")
        record_map[cid].append(entry)
    return dict(record_map)


def _sort_key(cid: str) -> int:
    return int(cid) if cid.isdigit() else 0


# ---------------------------------------------------------------------------
# Page 1 — Pipeline Run Summary (DB)
# ---------------------------------------------------------------------------


def _page_run_summary_db() -> None:
    st.title("Pipeline Run Summary")

    runs_df = _load_ingestion_runs()
    if runs_df.empty:
        st.warning("No ingestion runs found in the database yet.")
        return

    # -- Run selector
    run_options = []
    for _, row in runs_df.iterrows():
        started = row["started_at"]
        if isinstance(started, datetime):
            started = started.strftime("%Y-%m-%d %H:%M")
        run_options.append(f"{row['run_id']}  |  {row['source']}  |  {started}  |  {row['status']}")

    selected_idx = st.selectbox(
        "Select an ingestion run", range(len(run_options)), format_func=lambda i: run_options[i]
    )
    selected_run_id = runs_df.iloc[selected_idx]["run_id"]
    run_row = runs_df.iloc[selected_idx]

    st.markdown("---")

    # -- Headline metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Fetched", int(run_row["total_fetched"]))
    col2.metric("Staged", int(run_row["staged_count"]))
    col3.metric("Deduplicated", int(run_row["dedup_count"]))
    col4.metric("Errors", int(run_row["error_count"]))

    status = run_row["status"]
    if status == "success":
        st.success(f"Run `{selected_run_id}` completed successfully.")
    elif status == "running":
        st.info(f"Run `{selected_run_id}` is still running.")
    else:
        st.error(f"Run `{selected_run_id}` status: {status}")
        if run_row.get("error_message"):
            st.code(run_row["error_message"])

    st.markdown("---")

    # -- Stage completion: raw -> normalized
    raw_df = _load_raw_jobs(selected_run_id)
    norm_df = _load_normalized_jobs(selected_run_id)
    quarantine_df = _load_quarantined(selected_run_id)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Raw Ingested", len(raw_df))
    col_b.metric("Normalized", len(norm_df))
    col_c.metric("Quarantined", len(quarantine_df))

    st.markdown("---")

    # -- Completion table: one row per raw job showing stage progress
    st.subheader("Record Completion")
    st.caption("Each row is one ingested record. Columns show pipeline stage status.")

    if raw_df.empty:
        st.info("No records in this run.")
        return

    # Build normalized lookup by raw_job_id
    norm_raw_ids = set(norm_df["raw_job_id"].dropna().astype(int)) if not norm_df.empty else set()
    quarantine_raw_ids = set(quarantine_df["raw_job_id"].dropna().astype(int)) if not quarantine_df.empty else set()

    rows = []
    for _, raw in raw_df.iterrows():
        raw_id = int(raw["id"])
        ingested = raw["processing_status"] == "success"
        normalized = raw_id in norm_raw_ids
        quarantined = raw_id in quarantine_raw_ids

        rows.append(
            {
                "ID": raw_id,
                "Title": raw["title"],
                "Company": raw["company"],
                "Source": raw["source"],
                "Ingestion": "Pass" if ingested else "Fail",
                "Normalization": "Quarantined" if quarantined else ("Pass" if normalized else "Pending"),
            }
        )

    result_df = pd.DataFrame(rows)
    st.dataframe(result_df, use_container_width=True, hide_index=True)

    ingested_pass = sum(1 for r in rows if r["Ingestion"] == "Pass")
    norm_pass = sum(1 for r in rows if r["Normalization"] == "Pass")
    total = len(rows)
    st.info(f"Ingestion: {ingested_pass}/{total} passed  |  Normalization: {norm_pass}/{total} passed")


# ---------------------------------------------------------------------------
# Page 2 — Record Journey (DB)
# ---------------------------------------------------------------------------


def _page_record_journey_db() -> None:
    st.title("Record Journey")

    raw_df = _load_raw_jobs()
    if raw_df.empty:
        st.warning("No ingested records in the database yet.")
        return

    # -- Record selector
    options = []
    for _, row in raw_df.head(100).iterrows():
        options.append(f"[{row['id']}]  {row['title']}  @  {row['company']}")

    selected_idx = st.selectbox("Select a record to trace", range(len(options)), format_func=lambda i: options[i])
    selected_raw = raw_df.iloc[selected_idx]
    raw_id = int(selected_raw["id"])

    st.markdown("---")
    st.subheader(f"Record ID: `{raw_id}`  —  {selected_raw['title']}")
    st.caption(f"Source: {selected_raw['source']}  |  External ID: {selected_raw['external_id']}")

    # -- Stage 1: Ingestion
    st.markdown("#### Stage 1: Ingestion")
    with st.expander("Ingestion details", expanded=True):
        col1, col2 = st.columns(2)
        col1.markdown(f"**Run ID:** `{selected_raw['ingestion_run_id']}`")
        col2.markdown(f"**Status:** `{selected_raw['processing_status']}`")

        ingestion_fields = {
            "Title": selected_raw["title"],
            "Company": selected_raw["company"],
            "Location": ", ".join(
                filter(
                    None,
                    [
                        selected_raw.get("city"),
                        selected_raw.get("state"),
                        selected_raw.get("country"),
                    ],
                )
            )
            or "—",
            "Remote": selected_raw.get("is_remote"),
            "Date Posted": selected_raw.get("date_posted"),
            "Employment Type": selected_raw.get("employment_type"),
            "Experience Level": selected_raw.get("experience_level"),
            "Ingested At": selected_raw.get("ingestion_timestamp"),
        }
        st.json({k: str(v) if v is not None else "—" for k, v in ingestion_fields.items()})

        if selected_raw.get("salary_min") or selected_raw.get("salary_max"):
            st.markdown(
                f"**Salary:** {selected_raw.get('salary_min', '?')} – "
                f"{selected_raw.get('salary_max', '?')} "
                f"{selected_raw.get('salary_currency', '')} / "
                f"{selected_raw.get('salary_period', '')}"
            )

        if selected_raw.get("error_message"):
            st.error(f"Error: {selected_raw['error_message']}")

    # -- Stage 2: Normalization
    st.markdown("#### Stage 2: Normalization")
    norm_df = _load_normalized_jobs()
    norm_match = norm_df[norm_df["raw_job_id"] == raw_id] if not norm_df.empty else pd.DataFrame()

    if not norm_match.empty:
        norm_row = norm_match.iloc[0]
        with st.expander("Normalization details", expanded=True):
            col1, col2 = st.columns(2)
            col1.markdown(f"**Status:** `{norm_row['normalization_status']}`")
            col2.markdown(f"**Normalized ID:** `{norm_row['id']}`")

            norm_fields = {
                "Title": norm_row["title"],
                "Company": norm_row["company"],
                "Location": ", ".join(
                    filter(
                        None,
                        [
                            norm_row.get("city"),
                            norm_row.get("state_province"),
                            norm_row.get("country"),
                        ],
                    )
                )
                or "—",
                "Work Arrangement": norm_row.get("work_arrangement") or "—",
                "Remote": norm_row.get("is_remote"),
                "Employment Type": norm_row.get("employment_type") or "—",
                "Experience Level": norm_row.get("experience_level") or "—",
                "Date Posted": str(norm_row.get("date_posted")) if norm_row.get("date_posted") else "—",
            }
            st.json({k: str(v) if v is not None else "—" for k, v in norm_fields.items()})

            if norm_row.get("salary_min") or norm_row.get("salary_max"):
                st.markdown(
                    f"**Salary:** {norm_row.get('salary_min', '?')} – "
                    f"{norm_row.get('salary_max', '?')} "
                    f"{norm_row.get('salary_currency', '')} / "
                    f"{norm_row.get('salary_period', '')}"
                )
    else:
        # Check quarantine
        quarantine_df = _load_quarantined()
        q_match = quarantine_df[quarantine_df["raw_job_id"] == raw_id] if not quarantine_df.empty else pd.DataFrame()
        if not q_match.empty:
            q_row = q_match.iloc[0]
            with st.expander("Normalization — QUARANTINED", expanded=True):
                st.error(f"**Error type:** {q_row['error_type']}")
                st.code(q_row.get("error_detail", "No detail"))
        else:
            st.info("Not yet normalized — pending or in progress.")

    # -- Stages 3-7: Not yet in DB (future weeks)
    st.markdown("---")
    st.caption(
        "Stages 3–7 (Skills Extraction, Enrichment, Analytics, Visualization, Orchestration) "
        "will appear here as those agents write to the database in upcoming weeks."
    )


# ---------------------------------------------------------------------------
# Page 3 — Batch Insights (DB)
# ---------------------------------------------------------------------------


def _page_batch_insights_db() -> None:
    st.title("Batch Insights")
    st.caption("Aggregate view across ingested and normalized job records from the database.")

    norm_df = _load_normalized_jobs()
    raw_df = _load_raw_jobs()

    if norm_df.empty and raw_df.empty:
        st.warning("No records found in the database yet.")
        return

    # Use normalized if available, otherwise raw
    df = norm_df if not norm_df.empty else raw_df
    source_label = "normalized" if not norm_df.empty else "raw ingested"

    st.info(f"Showing aggregates from **{len(df)}** {source_label} records.")
    st.markdown("---")

    # -- Source distribution
    st.subheader("Source Distribution")
    if "source" in df.columns:
        source_counts = df["source"].value_counts()
        st.bar_chart(source_counts)

    st.markdown("---")

    # -- Locations
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Locations (State)")
        state_col = "state_province" if "state_province" in df.columns else "state"
        if state_col in df.columns:
            state_counts = df[state_col].dropna().value_counts().head(15)
            if not state_counts.empty:
                st.bar_chart(state_counts)
            else:
                st.info("No location data.")
        else:
            st.info("No state column found.")

    with col2:
        st.subheader("Top Cities")
        if "city" in df.columns:
            city_counts = df["city"].dropna().value_counts().head(15)
            if not city_counts.empty:
                st.bar_chart(city_counts)
            else:
                st.info("No city data.")

    st.markdown("---")

    # -- Remote distribution
    st.subheader("Remote vs On-site")
    if "is_remote" in df.columns:
        remote_counts = df["is_remote"].map({True: "Remote", False: "On-site", None: "Unknown"})
        remote_counts = remote_counts.fillna("Unknown").value_counts()
        st.bar_chart(remote_counts)

    st.markdown("---")

    # -- Employment type + Experience level (side by side)
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Employment Type")
        if "employment_type" in df.columns:
            et_counts = df["employment_type"].dropna().value_counts()
            if not et_counts.empty:
                st.bar_chart(et_counts)
            else:
                st.info("No employment type data.")

    with col4:
        st.subheader("Experience Level")
        if "experience_level" in df.columns:
            el_counts = df["experience_level"].dropna().value_counts()
            if not el_counts.empty:
                st.bar_chart(el_counts)
            else:
                st.info("No experience level data.")

    st.markdown("---")

    # -- Salary distribution
    st.subheader("Salary Distribution")
    salary_df = df[["salary_min", "salary_max"]].dropna(how="all")
    if not salary_df.empty:
        col_s1, col_s2, col_s3 = st.columns(3)
        valid_min = salary_df["salary_min"].dropna()
        valid_max = salary_df["salary_max"].dropna()
        if not valid_min.empty:
            col_s1.metric("Median Min Salary", f"${valid_min.median():,.0f}")
        if not valid_max.empty:
            col_s2.metric("Median Max Salary", f"${valid_max.median():,.0f}")
        col_s3.metric("Records with Salary", len(salary_df))

        # Histogram of salary_min
        if not valid_min.empty:
            st.markdown("**Minimum Salary Distribution**")
            st.bar_chart(valid_min.value_counts(bins=10).sort_index())
    else:
        st.info("No salary data available.")

    st.markdown("---")

    # -- Processing status (raw jobs)
    if not raw_df.empty and "processing_status" in raw_df.columns:
        st.subheader("Processing Status (Raw Jobs)")
        status_counts = raw_df["processing_status"].value_counts()
        st.bar_chart(status_counts)

    st.markdown("---")

    # -- Recent records table
    st.subheader("Recent Records")
    display_cols = ["title", "company", "source"]
    if "city" in df.columns:
        display_cols.append("city")
    state_col = "state_province" if "state_province" in df.columns else "state"
    if state_col in df.columns:
        display_cols.append(state_col)
    if "employment_type" in df.columns:
        display_cols.append("employment_type")
    if "experience_level" in df.columns:
        display_cols.append("experience_level")

    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[available_cols].head(50), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# JSON fallback pages (Week 2 walking skeleton)
# ---------------------------------------------------------------------------


def _page_run_summary_json(entries: list[dict]) -> None:
    st.title("Pipeline Run Summary")
    st.warning("Database unavailable — showing data from JSON file.")

    if not entries:
        st.error(
            f"No run log found at `{_RUN_LOG_PATH}`.  \n"
            "Run the pipeline first:  \n"
            "```\npython agents/pipeline_runner.py\n```"
        )
        return

    record_map = _build_record_map(entries)
    phase1_agents = [a for a in _AGENT_ORDER if a != "demand-analysis-agent"]

    timestamps = [e["timestamp"] for e in entries if "timestamp" in e]
    run_start = min(timestamps) if timestamps else "—"
    run_end = max(timestamps) if timestamps else "—"

    duration_str = "—"
    if run_start != "—" and run_end != "—":
        t0 = datetime.fromisoformat(run_start).replace(tzinfo=None)
        t1 = datetime.fromisoformat(run_end).replace(tzinfo=None)
        delta = t1 - t0
        total_seconds = delta.total_seconds()
        if total_seconds < 1:
            duration_str = f"{total_seconds * 1000:.0f} ms"
        elif total_seconds < 60:
            duration_str = f"{total_seconds:.2f} s"
        else:
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            duration_str = f"{minutes}m {seconds:.1f}s"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Records processed", len(record_map))
    col2.metric("Total log entries", len(entries))
    col3.metric("Run timestamp", run_start[:19] if run_start != "—" else "—")
    col4.metric("Duration", duration_str)
    st.markdown("---")

    st.subheader("Completion Table")
    st.caption(
        "One row per job record.  Each column is one pipeline stage.  "
        "Pass = event logged   Fail = stage missing or skipped"
    )

    rows = []
    for cid in sorted(record_map.keys(), key=_sort_key):
        record_entries = record_map[cid]
        completed_agents = {e["agent_id"] for e in record_entries}

        title, company = "—", "—"
        for e in record_entries:
            p = e.get("payload", {})
            if not title or title == "—":
                title = p.get("title") or title
            if not company or company == "—":
                company = p.get("company") or company
            if title != "—" and company != "—":
                break

        row: dict = {"Correlation ID": cid, "Title": title, "Company": company}
        for agent in phase1_agents:
            short = agent.replace("-agent", "").replace("-", " ").title()
            row[short] = "Pass" if agent in completed_agents else "Fail"

        all_phase1_done = all(a in completed_agents for a in phase1_agents)
        row["All Stages"] = "Pass" if all_phase1_done else "Fail"
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    complete_count = sum(1 for r in rows if r["All Stages"] == "Pass")
    total_count = len(rows)
    if complete_count == total_count:
        st.success(f"All {total_count} records completed all seven Phase 1 stages.")
    else:
        st.warning(f"{complete_count} / {total_count} records completed all Phase 1 stages.")


def _page_record_journey_json(entries: list[dict]) -> None:
    st.title("Record Journey")
    st.warning("Database unavailable — showing data from JSON file.")

    if not entries:
        st.error(
            f"No run log found at `{_RUN_LOG_PATH}`.  \n"
            "Run the pipeline first:  \n"
            "```\npython agents/pipeline_runner.py\n```"
        )
        return

    record_map = _build_record_map(entries)

    def label(cid: str) -> str:
        for e in record_map.get(cid, []):
            p = e.get("payload", {})
            t, c = p.get("title"), p.get("company")
            if t and c:
                return f"[{cid}]  {t}  @  {c}"
        return f"Record {cid}"

    sorted_cids = sorted(record_map.keys(), key=_sort_key)
    labels = [label(cid) for cid in sorted_cids]
    label_to_cid = dict(zip(labels, sorted_cids, strict=True))

    selected_label = st.selectbox("Select a record to trace", labels)
    selected_cid = label_to_cid[selected_label]

    st.markdown("---")
    st.subheader(f"Correlation ID: `{selected_cid}`")

    record_entries = sorted(
        record_map[selected_cid],
        key=lambda e: _AGENT_ORDER_INDEX.get(e.get("agent_id", ""), 99),
    )

    st.markdown("#### Stage-by-stage timeline")
    for entry in record_entries:
        agent_id = entry.get("agent_id", "—")
        payload = entry.get("payload", {})
        event_type = payload.get("event_type", agent_id)
        timestamp = entry.get("timestamp", "—")
        is_phase2 = event_type == "Phase2Skipped"

        status_str = "SKIPPED" if is_phase2 else "OK"
        label_str = f"{status_str}  **{agent_id}**  ->  `{event_type}`  |  {timestamp}"

        with st.expander(label_str, expanded=False):
            col_a, col_b = st.columns(2)
            col_a.markdown(f"**Event ID**  \n`{entry.get('event_id', '—')}`")
            col_b.markdown(f"**Schema Version**  \n`{entry.get('schema_version', '—')}`")
            st.markdown(f"**Correlation ID:** `{entry.get('correlation_id', '—')}`")

            if is_phase2:
                st.info("Phase 2 stub — this agent is not yet implemented.")
                continue

            summary_fields = [
                "event_type",
                "posting_id",
                "title",
                "company",
                "seniority",
                "role_classification",
                "quality_score",
                "spam_score",
                "is_spam",
                "normalization_status",
                "extraction_status",
                "enrichment_status",
                "render_status",
                "pipeline_stage",
                "run_id",
                "total_postings",
            ]
            summary = {k: payload[k] for k in summary_fields if k in payload}
            if summary:
                st.markdown("**Payload summary**")
                st.json(summary)

            skills = payload.get("skills")
            if skills:
                st.markdown("**Skills extracted**")
                st.dataframe(pd.DataFrame(skills), use_container_width=True, hide_index=True)

            top_skills = payload.get("top_skills")
            if top_skills:
                st.markdown("**Batch top skills** (from fixture analytics)")
                st.dataframe(pd.DataFrame(top_skills), use_container_width=True, hide_index=True)


def _page_batch_insights_json(entries: list[dict]) -> None:
    st.title("Batch Insights")
    st.warning("Database unavailable — showing data from JSON file.")

    if not entries:
        st.error(
            f"No run log found at `{_RUN_LOG_PATH}`.  \n"
            "Run the pipeline first:  \n"
            "```\npython agents/pipeline_runner.py\n```"
        )
        return

    analytics_entries = [e for e in entries if e.get("agent_id") == "analytics-agent"]
    if not analytics_entries:
        st.warning("No Analytics Agent entries found in the run log.")
        return

    p = analytics_entries[0].get("payload", {})

    st.subheader("Top Skills")
    top_skills = p.get("top_skills", [])
    if top_skills:
        df_skills = pd.DataFrame(top_skills).sort_values("count", ascending=False).set_index("skill")
        st.bar_chart(df_skills["count"])

    st.markdown("---")

    st.subheader("Seniority Distribution")
    seniority = p.get("seniority_distribution", {})
    if seniority:
        df_sen = (
            pd.DataFrame.from_dict(seniority, orient="index", columns=["count"])
            .reindex(["junior", "mid", "senior", "lead"])
            .dropna()
        )
        st.bar_chart(df_sen["count"])

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Role Distribution")
        roles = p.get("role_distribution", {})
        if roles:
            df_roles = (
                pd.DataFrame.from_dict(roles, orient="index", columns=["count"])
                .reset_index()
                .rename(columns={"index": "role"})
                .sort_values("count", ascending=False)
            )
            st.dataframe(df_roles, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Locations")
        locations = p.get("locations", {})
        if locations:
            df_loc = (
                pd.DataFrame.from_dict(locations, orient="index", columns=["postings"])
                .reset_index()
                .rename(columns={"index": "location"})
                .sort_values("postings", ascending=False)
            )
            st.dataframe(df_loc, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("Quality & Spam Scores")
    col3, col4 = st.columns(2)
    avg_quality = p.get("avg_quality_score")
    avg_spam = p.get("avg_spam_score")
    if avg_quality is not None:
        col3.metric("Average Quality Score", f"{avg_quality:.3f}")
    if avg_spam is not None:
        col4.metric("Average Spam Score", f"{avg_spam:.3f}")

    enrichment_entries = [e for e in entries if e.get("agent_id") == "enrichment-agent"]
    if enrichment_entries:
        st.markdown("#### Per-record quality breakdown")
        quality_rows = []
        for e in enrichment_entries:
            ep = e.get("payload", {})
            quality_rows.append(
                {
                    "Posting ID": ep.get("posting_id"),
                    "Title": ep.get("title"),
                    "Company": ep.get("company"),
                    "Role": ep.get("role_classification"),
                    "Seniority": ep.get("seniority"),
                    "Quality": ep.get("quality_score"),
                    "Spam": ep.get("spam_score"),
                    "Is Spam": ep.get("is_spam"),
                }
            )
        df_quality = pd.DataFrame(quality_rows).sort_values("Posting ID")
        st.dataframe(df_quality, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title="JIE Dashboard",
        page_icon="*",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.title("JIE Dashboard")

    # Detect data source — shown directly under title
    use_db = _db_available()
    if use_db:
        st.sidebar.success("Connected to PostgreSQL")
    else:
        st.sidebar.warning("Using fixture data (JSON)")
        st.sidebar.caption("Set `PYTHON_DATABASE_URL` in `.env` to connect to PostgreSQL.")

    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigate",
        options=[
            "Pipeline Run Summary",
            "Record Journey",
            "Batch Insights",
        ],
    )

    if use_db:
        if page == "Pipeline Run Summary":
            _page_run_summary_db()
        elif page == "Record Journey":
            _page_record_journey_db()
        elif page == "Batch Insights":
            _page_batch_insights_db()
    else:
        entries = _load_run_log()
        if page == "Pipeline Run Summary":
            _page_run_summary_json(entries)
        elif page == "Record Journey":
            _page_record_journey_json(entries)
        elif page == "Batch Insights":
            _page_batch_insights_json(entries)


if __name__ == "__main__":
    main()
