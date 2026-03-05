"""
Streamlit dashboard — pipeline run viewer.
Loads agents/data/output/pipeline_run.json; System Overview, Record Journey, Batch Insights.
Safe handling for null posting_id and analytics batch payloads.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

PIPELINE_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "output" / "pipeline_run.json"
)


@st.cache_data
def load_pipeline_run() -> list[dict] | None:
    """Load pipeline run JSON. Returns None if file missing."""
    if not PIPELINE_OUTPUT_PATH.exists():
        return None
    try:
        with open(PIPELINE_OUTPUT_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main() -> None:
    data = load_pipeline_run()
    if data is None:
        st.error(
            "Pipeline output not found. Run the pipeline first: "
            "`python -m agents.pipeline_runner` (from repo root)."
        )
        st.stop()

    st.sidebar.title("Pipeline Dashboard")
    page = st.sidebar.radio(
        "Page",
        ["System Overview", "Record Journey", "Batch Insights"],
        label_visibility="collapsed",
    )

    if page == "System Overview":
        _render_system_overview(data)
    elif page == "Record Journey":
        _render_record_journey(data)
    else:
        _render_batch_insights(data)


def _render_system_overview(data: list[dict]) -> None:
    st.header("System Overview")
    try:
        total_events = len(data)
        unique_records = len({e.get("correlation_id", "") for e in data if e.get("correlation_id")})
    except Exception:
        total_events = 0
        unique_records = 0
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Events", total_events)
    with col2:
        st.metric("Unique Job Records", unique_records)

    try:
        df = pd.DataFrame(data)
    except Exception:
        st.warning("Could not build DataFrame from pipeline data.")
        return
    if "agent_id" in df.columns:
        agent_counts = df["agent_id"].value_counts()
        st.subheader("Events by agent")
        chart_df = agent_counts.rename_axis("agent_id").reset_index(name="count")
        st.bar_chart(chart_df.set_index("agent_id"))
    st.subheader("Run data (preview)")
    st.dataframe(df.head(20))


def _render_record_journey(data: list[dict]) -> None:
    st.header("Record Journey")
    try:
        correlation_ids = sorted({e.get("correlation_id", "") for e in data if e.get("correlation_id")})
    except Exception:
        correlation_ids = []
    if not correlation_ids:
        st.warning("No correlation IDs in pipeline run.")
        return
    selected_id = st.selectbox(
        "Select job record (correlation_id)",
        correlation_ids,
        format_func=lambda cid: (cid[:8] + "…") if cid and len(cid) > 8 else (cid or "N/A"),
    )
    try:
        steps = [e for e in data if e.get("correlation_id") == selected_id]
        steps.sort(key=lambda e: e.get("timestamp", ""))
    except Exception:
        steps = []
        st.warning("Could not filter events by correlation_id.")

    st.caption(f"Showing {len(steps)} steps for this record.")
    for step in steps:
        try:
            agent_id = step.get("agent_id", "?")
            ts = step.get("timestamp", "")
            is_phase2_skip = step.get("phase2_skipped") is True
            label = f"{agent_id} — {ts}"
            if is_phase2_skip:
                label = f"{agent_id} (Skipped — Phase 2) — {ts}"
        except Exception:
            agent_id = "?"
            label = "Unknown step"
            is_phase2_skip = False
        with st.expander(label):
            if is_phase2_skip:
                st.warning("Skipped (Phase 2). Demand Analysis agent is not implemented.")
            try:
                summary = f"Agent: **{agent_id}**. "
                if is_phase2_skip:
                    summary += "This step was skipped (Phase 2)."
                else:
                    payload = step.get("payload", {})
                    pid = payload.get("posting_id", "N/A")
                    summary += f"posting_id in payload: {pid}."
                st.markdown(summary)
            except Exception:
                st.caption("Summary unavailable.")
            try:
                if is_phase2_skip:
                    st.json({k: v for k, v in step.items()})
                else:
                    st.json(step.get("payload", {}))
            except Exception:
                st.caption("Payload unavailable.")


def _render_batch_insights(data: list[dict]) -> None:
    st.header("Batch Insights")

    # 1. Data extraction: first analytics event payload
    analytics_event = None
    try:
        for e in data:
            if e.get("agent_id") == "analytics":
                analytics_event = e
                break
    except Exception:
        pass
    if not analytics_event:
        st.warning("No analytics event found in pipeline run.")
        return
    try:
        payload = analytics_event.get("payload") or {}
    except Exception:
        payload = {}

    # Layout: two columns for a clean grid (row 1: skills + seniority, row 2: locations + companies)
    col1, col2 = st.columns(2)

    # Chart 1: Top skills (bar chart)
    with col1:
        st.subheader("Top skills")
        try:
            top_skills = payload.get("top_skills") or []
            if top_skills and isinstance(top_skills, list):
                skills_df = pd.DataFrame(top_skills)
                if "skill" in skills_df.columns and "count" in skills_df.columns:
                    skills_df = skills_df[["skill", "count"]]
                    st.bar_chart(skills_df.set_index("skill"))
                else:
                    st.warning("top_skills missing 'skill' or 'count'.")
            else:
                st.warning("No top_skills in analytics payload.")
        except Exception:
            st.warning("Could not render top skills chart.")

    # Chart 2: Seniority distribution (bar chart)
    with col2:
        st.subheader("Seniority distribution")
        try:
            seniority = payload.get("seniority_distribution") or {}
            if seniority and isinstance(seniority, dict):
                seniority_df = pd.DataFrame(
                    [{"seniority": k, "count": v} for k, v in seniority.items()]
                )
                if not seniority_df.empty:
                    st.bar_chart(seniority_df.set_index("seniority"))
                else:
                    st.warning("seniority_distribution is empty.")
            else:
                st.warning("No seniority_distribution in analytics payload.")
        except Exception:
            st.warning("Could not render seniority chart.")

    # Second row: locations and companies
    col3, col4 = st.columns(2)

    # Chart 3: Locations represented
    with col3:
        st.subheader("Locations represented")
        try:
            locations = payload.get("locations") or {}
            if locations and isinstance(locations, dict):
                locations_df = pd.DataFrame(
                    [{"location": k, "count": v} for k, v in locations.items()]
                )
                if not locations_df.empty:
                    st.bar_chart(locations_df.set_index("location"))
                else:
                    st.warning("locations is empty.")
            else:
                st.warning("No locations in analytics payload.")
        except Exception:
            st.warning("Could not render locations chart.")

    # Chart 4: Companies represented (from ingestion events, not analytics payload)
    with col4:
        st.subheader("Companies represented")
        try:
            companies = []
            for e in data:
                if e.get("agent_id") != "ingestion":
                    continue
                p = e.get("payload") or {}
                company = p.get("company")
                if company:
                    companies.append(company)
            if companies:
                counts = Counter(companies)
                companies_df = pd.DataFrame(
                    [{"company": k, "count": v} for k, v in counts.most_common()]
                )
                if not companies_df.empty:
                    st.bar_chart(companies_df.set_index("company"))
                else:
                    st.warning("No company data from ingestion events.")
            else:
                st.warning("No companies found in ingestion events.")
        except Exception:
            st.warning("Could not render companies chart.")


if __name__ == "__main__":
    main()
