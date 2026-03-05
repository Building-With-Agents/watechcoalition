"""
Streamlit dashboard — Pipeline run viewer.

Uses agents/data/output/pipeline_run.json as the data source.
Three pages: Pipeline Run Summary, Record Journey, Batch Insights.
Run with: streamlit run agents/dashboard/streamlit_app.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

_AGENTS_DIR = Path(__file__).resolve().parent.parent
PIPELINE_RUN_PATH = _AGENTS_DIR / "data" / "output" / "pipeline_run.json"

CANONICAL_AGENT_IDS = [
    "ingestion",
    "normalization",
    "skills_extraction",
    "enrichment",
    "analytics",
    "visualization",
    "orchestration",
    "demand_analysis",
]


@st.cache_data(ttl=60)
def load_pipeline_run() -> list[dict[str, Any]] | None:
    """Load pipeline_run.json; return list of entries or None if missing/invalid."""
    if not PIPELINE_RUN_PATH.exists():
        return None
    try:
        with open(PIPELINE_RUN_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _no_data_placeholder() -> None:
    st.warning(
        "No pipeline run data found. Run the pipeline to generate data: "
        "`python -m agents.pipeline_runner`"
    )
    st.caption(f"Expected file: `{PIPELINE_RUN_PATH}`")


def page_pipeline_summary() -> None:
    st.title("Pipeline Run Summary")
    data = load_pipeline_run()
    if not data:
        _no_data_placeholder()
        return

    total = len(data)
    unique_records = len({e.get("correlation_id") for e in data if e.get("correlation_id") is not None})
    failed_count = sum(1 for e in data if e.get("status") == "failed")
    skipped_count = sum(1 for e in data if e.get("status") == "skipped")
    ok_count = sum(1 for e in data if e.get("status") == "ok")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total entries", total)
    with c2:
        st.metric("Unique records", unique_records)
    with c3:
        st.metric("OK", ok_count)
    with c4:
        if failed_count > 0:
            st.error(f"Failed: {failed_count}")
        else:
            st.metric("Failed", failed_count)
    st.metric("Skipped", skipped_count)

    st.subheader("Per-agent breakdown")
    for agent_id in CANONICAL_AGENT_IDS:
        agent_entries = [e for e in data if e.get("agent_id") == agent_id]
        a_ok = sum(1 for e in agent_entries if e.get("status") == "ok")
        a_skipped = sum(1 for e in agent_entries if e.get("status") == "skipped")
        a_failed = sum(1 for e in agent_entries if e.get("status") == "failed")
        failed_list = [e for e in agent_entries if e.get("status") == "failed"]

        if failed_list:
            with st.expander(f"**{agent_id}** — ok: {a_ok}, skipped: {a_skipped}, failed: {a_failed}", expanded=True):
                for e in failed_list:
                    st.markdown(
                        f"- `correlation_id={e.get('correlation_id')}` "
                        f"`posting_id={e.get('posting_id')}` — {e.get('error', '')}"
                    )
        else:
            st.markdown(f"**{agent_id}** — ok: {a_ok}, skipped: {a_skipped}, failed: {a_failed}")

    failed_entries = [e for e in data if e.get("status") == "failed"]
    if failed_entries:
        st.subheader("Errors")
        with st.expander("All failed entries", expanded=True):
            rows = [
                {
                    "correlation_id": e.get("correlation_id"),
                    "posting_id": e.get("posting_id"),
                    "agent_id": e.get("agent_id"),
                    "error": e.get("error", ""),
                    "timestamp": e.get("timestamp"),
                }
                for e in failed_entries
            ]
            st.dataframe(rows, use_container_width=True)


def page_record_journey() -> None:
    st.title("Record Journey")
    data = load_pipeline_run()
    if not data:
        _no_data_placeholder()
        return

    records = sorted(
        {(e.get("correlation_id"), e.get("posting_id")) for e in data if e.get("correlation_id") is not None},
        key=lambda x: (str(x[0]), x[1]),
    )
    if not records:
        st.info("No records in the run log.")
        return

    options = [f"Record {cid} (posting_id {pid})" for cid, pid in records]
    option_to_pair = dict(zip(options, records))
    selected = st.selectbox("Select a record", options=options, key="record_journey_select")
    if not selected:
        return
    cid, pid = option_to_pair[selected]

    entries = [e for e in data if e.get("correlation_id") == cid]
    ordered = []
    for agent_id in CANONICAL_AGENT_IDS:
        for e in entries:
            if e.get("agent_id") == agent_id:
                ordered.append(e)
                break

    st.subheader(f"Timeline for record {cid}")
    if not ordered:
        st.caption("No steps found for this record.")
        return

    table_data = []
    for e in ordered:
        table_data.append({
            "Agent": e.get("agent_id", ""),
            "Status": e.get("status", ""),
            "Timestamp": e.get("timestamp", ""),
            "Error": e.get("error", "") or "—",
        })
    st.dataframe(table_data, use_container_width=True)

    for e in ordered:
        status = e.get("status", "")
        err = e.get("error", "")
        if status == "failed" and err:
            st.error(f"**{e.get('agent_id')}** failed: {err}")


def page_batch_insights() -> None:
    st.title("Batch Insights")
    data = load_pipeline_run()
    if not data:
        _no_data_placeholder()
        return

    total = len(data)
    unique_records = len({e.get("correlation_id") for e in data if e.get("correlation_id") is not None})
    num_agents = len(CANONICAL_AGENT_IDS)
    expected = unique_records * num_agents if unique_records and num_agents else 0

    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total run-log entries", total)
    with col2:
        st.metric("Unique records", unique_records)
    with col3:
        st.metric("Expected (records × 8 agents)", expected)
    if expected and total != expected:
        st.caption(f"Actual entries: {total} (expected {expected})")

    st.subheader("Status counts")
    ok_count = sum(1 for e in data if e.get("status") == "ok")
    skipped_count = sum(1 for e in data if e.get("status") == "skipped")
    failed_count = sum(1 for e in data if e.get("status") == "failed")
    status_df = {"Status": ["ok", "skipped", "failed"], "Count": [ok_count, skipped_count, failed_count]}
    st.bar_chart(status_df, x="Status", y="Count")

    st.subheader("By agent")
    rows = []
    for agent_id in CANONICAL_AGENT_IDS:
        agent_entries = [e for e in data if e.get("agent_id") == agent_id]
        rows.append({
            "agent": agent_id,
            "ok": sum(1 for e in agent_entries if e.get("status") == "ok"),
            "skipped": sum(1 for e in agent_entries if e.get("status") == "skipped"),
            "failed": sum(1 for e in agent_entries if e.get("status") == "failed"),
        })
    st.dataframe(rows, use_container_width=True)

    chart_data = {"agent": [r["agent"] for r in rows], "ok": [r["ok"] for r in rows], "skipped": [r["skipped"] for r in rows], "failed": [r["failed"] for r in rows]}
    st.bar_chart(chart_data, x="agent", y=["ok", "skipped", "failed"])


def main() -> None:
    st.set_page_config(page_title="Pipeline Dashboard", page_icon="📊", layout="wide")
    nav = st.navigation([
        st.Page(page_pipeline_summary, title="Pipeline Run Summary", default=True),
        st.Page(page_record_journey, title="Record Journey"),
        st.Page(page_batch_insights, title="Batch Insights"),
    ])
    nav.run()


if __name__ == "__main__":
    main()
