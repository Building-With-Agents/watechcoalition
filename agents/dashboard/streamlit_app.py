"""
Journey Dashboard — Database-connected Streamlit dashboard.

Multi-page Streamlit dashboard for observing pipeline data.

Pages
-----
1. Ingestion Overview / Normalization Quality (Week 6) — pipeline health.
2. Pipeline Run Summary   — ingestion runs, record counts, stage completion.
3. Record Journey         — select one record and trace it through stages.
4. Batch Insights         — aggregate charts: locations, employment types,
                            experience levels, salary distributions, sources.
5. Weekly Insights (Week 7) — `skill_demand_weekly` top skills by week.

Data source: PostgreSQL (via SQLAlchemy) with JSON file fallback.

Usage:
    streamlit run agents/dashboard/app.py
    # or: streamlit run agents/dashboard/streamlit_app.py
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from agents.common.env import load_repo_root_dotenv
from agents.dashboard.batch_insights_queries import (
    fetch_batch_insights_bundle,
    series_from_category_count,
    series_from_salary_histogram,
)
from agents.dashboard.relation_safe import read_sql_relation_safe

# ---------------------------------------------------------------------------
# Environment & paths
# ---------------------------------------------------------------------------

load_repo_root_dotenv()

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

# Values written by ingestion (pending) and normalization (normalized | quarantined) on dbo.raw_ingested_jobs.
_RAW_STAGED_OK_STATUSES = frozenset({"pending", "normalized", "quarantined", "success"})


def _raw_row_ingestion_succeeded(processing_status: object) -> bool:
    """True when the raw row exists in a post-staging pipeline state (not a failed-ingest marker)."""
    return str(processing_status or "").strip().lower() in _RAW_STAGED_OK_STATUSES


def _clamp_list_window(limit: int, offset: int) -> tuple[int, int]:
    """Bound Streamlit-driven LIMIT/OFFSET for unscoped raw/normalized list queries."""
    lim = max(1, min(int(limit), 5000))
    off = max(0, int(offset))
    return lim, off


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _db_available() -> bool:
    """Check if PostgreSQL is reachable via the dashboard read-only engine."""
    if not (os.getenv("PYTHON_DATABASE_URL") or os.getenv("PYTHON_DATABASE_URL_READONLY")):
        return False
    try:
        from agents.dashboard.readonly_engine import check_dashboard_db_connection

        return check_dashboard_db_connection()
    except Exception:
        return False


@st.cache_data(ttl=300, show_spinner=False)
def _load_ingestion_runs() -> tuple[pd.DataFrame, str | None]:
    """Load ingestion run history from DB.

    Returns ``(dataframe, optional_warning)`` when ``dbo.job_ingestion_runs`` is missing.
    """
    from agents.dashboard.readonly_engine import get_dashboard_engine

    query = """
        SELECT run_id, region_id, source, started_at, completed_at,
               status, total_fetched, staged_count, dedup_count, error_count,
               error_message
        FROM dbo.job_ingestion_runs
        ORDER BY started_at DESC
        LIMIT 50
    """
    return read_sql_relation_safe(
        query,
        get_dashboard_engine(),
        user_hint="`dbo.job_ingestion_runs` is missing. Apply agent migrations or run the Ingestion agent to create pipeline tables.",
    )


@st.cache_data(ttl=300, show_spinner=False)
def _load_raw_jobs(
    run_id: str | None = None,
    *,
    limit: int = 500,
    offset: int = 0,
) -> tuple[pd.DataFrame, str | None]:
    """Load raw ingested jobs, optionally filtered by run_id.

    When ``run_id`` is set, returns all rows for that run (no limit — typical batches are small).
    Otherwise returns a newest-first window: ``LIMIT`` / ``OFFSET`` (for Record Journey paging).

    Returns ``(dataframe, optional_warning)`` when ``dbo.raw_ingested_jobs`` is missing.
    """
    from agents.dashboard.readonly_engine import get_dashboard_engine

    engine = get_dashboard_engine()
    hint = (
        "`dbo.raw_ingested_jobs` is missing. Apply agent migrations or run the Ingestion agent "
        "to create staging tables."
    )
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
        return read_sql_relation_safe(query, engine, params={"run_id": run_id}, user_hint=hint)
    lim, off = _clamp_list_window(limit, offset)
    query = """
        SELECT id, ingestion_run_id, region_id, source, external_id,
               title, company, city, state, country, is_remote,
               date_posted, employment_type, experience_level,
               salary_min, salary_max, salary_currency, salary_period,
               processing_status, error_message, ingestion_timestamp
        FROM dbo.raw_ingested_jobs
        ORDER BY id DESC
        LIMIT %(lim)s OFFSET %(off)s
    """
    return read_sql_relation_safe(query, engine, params={"lim": lim, "off": off}, user_hint=hint)


@st.cache_data(ttl=300, show_spinner=False)
def _load_normalized_jobs(
    run_id: str | None = None,
    *,
    limit: int = 500,
    offset: int = 0,
) -> tuple[pd.DataFrame, str | None]:
    """Load normalized jobs, optionally filtered by run_id.

    Same window semantics as :func:`_load_raw_jobs`.
    Returns ``(dataframe, optional_warning)`` when ``dbo.normalized_jobs`` is missing.
    """
    from agents.dashboard.readonly_engine import get_dashboard_engine

    engine = get_dashboard_engine()
    hint = "`dbo.normalized_jobs` is missing. Apply agent migrations or run the Normalization agent."
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
        return read_sql_relation_safe(query, engine, params={"run_id": run_id}, user_hint=hint)
    lim, off = _clamp_list_window(limit, offset)
    query = """
        SELECT id, raw_job_id, ingestion_run_id, region_id, source, external_id,
               title, company, city, state_province, country,
               work_arrangement, is_remote, employment_type, experience_level,
               date_posted, salary_min, salary_max, salary_currency, salary_period,
               normalization_status, created_at
        FROM dbo.normalized_jobs
        ORDER BY id DESC
        LIMIT %(lim)s OFFSET %(off)s
    """
    return read_sql_relation_safe(query, engine, params={"lim": lim, "off": off}, user_hint=hint)


@st.cache_data(ttl=300, show_spinner=False)
def _load_normalized_for_raw_job(raw_job_id: int) -> tuple[pd.DataFrame, str | None]:
    """Load normalized row(s) for a single raw job (Record Journey with paged raw list)."""
    from agents.dashboard.readonly_engine import get_dashboard_engine

    q = """
        SELECT id, raw_job_id, ingestion_run_id, region_id, source, external_id,
               title, company, city, state_province, country,
               work_arrangement, is_remote, employment_type, experience_level,
               date_posted, salary_min, salary_max, salary_currency, salary_period,
               normalization_status, created_at
        FROM dbo.normalized_jobs
        WHERE raw_job_id = %(rid)s
        ORDER BY id DESC
        LIMIT 5
    """
    return read_sql_relation_safe(
        q,
        get_dashboard_engine(),
        params={"rid": int(raw_job_id)},
        user_hint="`dbo.normalized_jobs` is missing. Apply agent migrations or run the Normalization agent.",
    )


@st.cache_data(ttl=300, show_spinner=False)
def _load_quarantine_for_raw_job(raw_job_id: int) -> tuple[pd.DataFrame, str | None]:
    """Load quarantine row(s) for a single raw job."""
    from agents.dashboard.readonly_engine import get_dashboard_engine

    q = """
        SELECT id, raw_job_id, ingestion_run_id, source, external_id,
               error_type, error_detail, quarantined_at
        FROM dbo.normalization_quarantine
        WHERE raw_job_id = %(rid)s
        ORDER BY quarantined_at DESC
        LIMIT 5
    """
    return read_sql_relation_safe(
        q,
        get_dashboard_engine(),
        params={"rid": int(raw_job_id)},
        user_hint="`dbo.normalization_quarantine` is missing. Apply agent migrations.",
    )


@st.cache_data(ttl=300, show_spinner=False)
def _load_quarantined(run_id: str | None = None) -> tuple[pd.DataFrame, str | None]:
    """Load quarantined records."""
    from agents.dashboard.readonly_engine import get_dashboard_engine

    engine = get_dashboard_engine()
    hint = "`dbo.normalization_quarantine` is missing. Apply agent migrations."
    if run_id:
        query = """
            SELECT id, raw_job_id, ingestion_run_id, source, external_id,
                   error_type, error_detail, quarantined_at
            FROM dbo.normalization_quarantine
            WHERE ingestion_run_id = %(run_id)s
            ORDER BY quarantined_at DESC
        """
        return read_sql_relation_safe(query, engine, params={"run_id": run_id}, user_hint=hint)
    query = """
        SELECT id, raw_job_id, ingestion_run_id, source, external_id,
               error_type, error_detail, quarantined_at
        FROM dbo.normalization_quarantine
        ORDER BY quarantined_at DESC
        LIMIT 100
    """
    return read_sql_relation_safe(query, engine, user_hint=hint)


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

    runs_df, warn_runs = _load_ingestion_runs()
    if warn_runs:
        st.warning(warn_runs)
    if runs_df.empty:
        if not warn_runs:
            st.info("No ingestion runs found in the database yet.")
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
    if status in ("success", "completed"):
        st.success(f"Run `{selected_run_id}` completed successfully.")
    elif status == "running":
        st.info(f"Run `{selected_run_id}` is still running.")
    else:
        st.error(f"Run `{selected_run_id}` status: {status}")
        if run_row.get("error_message"):
            st.code(run_row["error_message"])

    st.markdown("---")

    # -- Stage completion: raw -> normalized
    raw_df, warn_raw = _load_raw_jobs(selected_run_id)
    norm_df, warn_norm = _load_normalized_jobs(selected_run_id)
    quarantine_df, warn_quarantine = _load_quarantined(selected_run_id)
    for w in dict.fromkeys((warn_raw, warn_norm, warn_quarantine)):
        if w:
            st.warning(w)

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
        ingested = _raw_row_ingestion_succeeded(raw.get("processing_status"))
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
    st.dataframe(result_df, width="stretch", hide_index=True)

    ingested_pass = sum(1 for r in rows if r["Ingestion"] == "Pass")
    norm_pass = sum(1 for r in rows if r["Normalization"] == "Pass")
    total = len(rows)
    st.info(f"Ingestion: {ingested_pass}/{total} passed  |  Normalization: {norm_pass}/{total} passed")


# ---------------------------------------------------------------------------
# Page 2 — Record Journey (DB)
# ---------------------------------------------------------------------------


def _page_record_journey_db() -> None:
    st.title("Record Journey")

    with st.expander("List window (newest raw rows first by id)", expanded=False):
        c1, c2 = st.columns(2)
        rj_limit = c1.number_input(
            "Max rows to load",
            min_value=50,
            max_value=5000,
            value=500,
            step=50,
            key="rj_raw_limit",
        )
        rj_offset = c2.number_input(
            "Skip first N rows (offset)",
            min_value=0,
            max_value=1_000_000,
            value=0,
            step=100,
            key="rj_raw_offset",
        )
        st.caption("Use offset to page into older raw ingested jobs. Normalization status is looked up per row in SQL.")

    raw_df, warn_raw = _load_raw_jobs(limit=int(rj_limit), offset=int(rj_offset))
    if warn_raw:
        st.warning(warn_raw)
    if raw_df.empty:
        if not warn_raw:
            st.info("No ingested records in this window — try a smaller offset or verify the database.")
        return

    lim_clamped, off_clamped = _clamp_list_window(int(rj_limit), int(rj_offset))
    st.caption(
        f"Loaded raw rows **{off_clamped + 1}–{off_clamped + len(raw_df)}** (limit {lim_clamped}, offset {off_clamped})."
    )

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
    norm_match, warn_norm = _load_normalized_for_raw_job(raw_id)

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
        if warn_norm:
            st.warning(warn_norm)
        q_match, warn_quarantine = _load_quarantine_for_raw_job(raw_id)
        if warn_quarantine:
            st.warning(warn_quarantine)
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
    st.caption(
        "Aggregate charts use **full-table SQL** (GROUP BY / percentiles). Recent records are a 50-row sample only."
    )

    try:
        bundle = fetch_batch_insights_bundle()
    except Exception as exc:
        st.error(f"Could not load batch insights: {exc}")
        return

    for msg in bundle.get("dashboard_soft_warnings") or []:
        st.warning(msg)

    total = int(bundle["total_rows"])
    if total <= 0:
        if bundle.get("dashboard_soft_warnings"):
            st.info("No job rows available for Batch Insights with the current database snapshot.")
        else:
            st.warning("No records found in the database yet.")
        return

    source_label = "normalized" if bundle["use_normalized"] else "raw ingested"
    st.info(f"**{total:,}** rows in **{source_label}** table — charts reflect all of them.")
    st.markdown("---")

    st.subheader("Source Distribution")
    sc = series_from_category_count(bundle["source_df"])
    if not sc.empty:
        st.bar_chart(sc)
    else:
        st.info("No source data.")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Locations (State)")
        stc = series_from_category_count(bundle["state_df"])
        if not stc.empty:
            st.bar_chart(stc)
        else:
            st.info("No location data.")

    with col2:
        st.subheader("Top Cities")
        cc = series_from_category_count(bundle["city_df"])
        if not cc.empty:
            st.bar_chart(cc)
        else:
            st.info("No city data.")

    st.markdown("---")

    st.subheader("Remote vs On-site")
    rc = series_from_category_count(bundle["remote_df"])
    if not rc.empty:
        st.bar_chart(rc)
    else:
        st.info("No remote flag data.")

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Employment Type")
        ec = series_from_category_count(bundle["employment_df"])
        if not ec.empty:
            st.bar_chart(ec)
        else:
            st.info("No employment type data.")

    with col4:
        st.subheader("Experience Level")
        xc = series_from_category_count(bundle["experience_df"])
        if not xc.empty:
            st.bar_chart(xc)
        else:
            st.info("No experience level data.")

    st.markdown("---")

    st.subheader("Salary Distribution")
    col_s1, col_s2, col_s3 = st.columns(3)
    med_min = bundle["median_min"]
    med_max = bundle["median_max"]
    if med_min is not None and not pd.isna(med_min):
        col_s1.metric("Median Min Salary", f"${float(med_min):,.0f}")
    else:
        col_s1.metric("Median Min Salary", "—")
    if med_max is not None and not pd.isna(med_max):
        col_s2.metric("Median Max Salary", f"${float(med_max):,.0f}")
    else:
        col_s2.metric("Median Max Salary", "—")
    col_s3.metric("Records with salary fields", f"{bundle['salary_rows']:,}")

    hist_df = bundle["salary_hist_df"]
    h_lo = bundle.get("salary_hist_lo")
    h_hi = bundle.get("salary_hist_hi")
    if not hist_df.empty and "cnt" in hist_df.columns and h_lo is not None and h_hi is not None:
        st.markdown("**Minimum salary (10 equal-width buckets)** — axis shows USD range per bucket.")
        h = series_from_salary_histogram(hist_df, float(h_lo), float(h_hi))
        st.bar_chart(h)
    elif bundle["salary_rows"] > 0:
        st.info("Not enough spread in salary_min for a histogram.")
    else:
        st.info("No salary data available.")

    st.markdown("---")

    st.subheader("Processing Status (all raw ingested jobs)")
    ps = series_from_category_count(bundle["raw_status_df"])
    if not ps.empty:
        st.bar_chart(ps)
    else:
        st.info("No raw rows.")

    st.markdown("---")

    st.subheader("Recent Records (50-row sample)")
    recent = bundle["recent_df"]
    if recent.empty:
        st.info("No recent rows.")
    else:
        st.dataframe(recent, width="stretch", hide_index=True)


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
    st.dataframe(df, width="stretch", hide_index=True)

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
                st.dataframe(pd.DataFrame(skills), width="stretch", hide_index=True)

            top_skills = payload.get("top_skills")
            if top_skills:
                st.markdown("**Batch top skills** (from fixture analytics)")
                st.dataframe(pd.DataFrame(top_skills), width="stretch", hide_index=True)


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
            st.dataframe(df_roles, width="stretch", hide_index=True)

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
            st.dataframe(df_loc, width="stretch", hide_index=True)

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
        st.dataframe(df_quality, width="stretch", hide_index=True)


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
        st.sidebar.success("Connected to PostgreSQL (read-only)")
    else:
        st.sidebar.warning("Using fixture data (JSON)")
        st.sidebar.caption("Set `PYTHON_DATABASE_URL` (or `PYTHON_DATABASE_URL_READONLY`) in `.env`.")

    st.sidebar.markdown("---")
    st.sidebar.caption("Week 6 — observability · Week 7 — weekly insights")
    page = st.sidebar.radio(
        "Navigate",
        options=[
            "Ingestion Overview",
            "Normalization Quality",
            "Pipeline Run Summary",
            "Record Journey",
            "Batch Insights",
            "Weekly Insights",
        ],
    )

    if use_db:
        if page == "Ingestion Overview":
            from agents.dashboard.pages_observability import render_ingestion_overview

            render_ingestion_overview()
        elif page == "Normalization Quality":
            from agents.dashboard.pages_observability import render_normalization_quality

            render_normalization_quality()
        elif page == "Pipeline Run Summary":
            _page_run_summary_db()
        elif page == "Record Journey":
            _page_record_journey_db()
        elif page == "Batch Insights":
            _page_batch_insights_db()
        elif page == "Weekly Insights":
            from agents.dashboard.pages_weekly_insights import render_weekly_insights

            render_weekly_insights()
    else:
        entries = _load_run_log()
        if page == "Weekly Insights":
            st.title("Weekly Insights")
            st.warning(
                "This page needs PostgreSQL aggregate tables. Set `PYTHON_DATABASE_URL` "
                "(or `PYTHON_DATABASE_URL_READONLY`) and restart the app."
            )
            st.info("Journey and Batch Insights (JSON) still work with `agents/data/output/pipeline_run.json`.")
        elif page in ("Ingestion Overview", "Normalization Quality"):
            st.title(page)
            st.warning("Week 6 observability pages require PostgreSQL. Set `PYTHON_DATABASE_URL` and restart the app.")
            st.info("Journey pages below still work with `agents/data/output/pipeline_run.json`.")
        elif page == "Pipeline Run Summary":
            _page_run_summary_json(entries)
        elif page == "Record Journey":
            _page_record_journey_json(entries)
        elif page == "Batch Insights":
            _page_batch_insights_json(entries)


if __name__ == "__main__":
    main()
