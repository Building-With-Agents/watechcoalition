"""
Journey Dashboard — Week 2 Walking Skeleton.

Three-page Streamlit dashboard for observing a pipeline run.

Pages
-----
1. Pipeline Run Summary   — did all records complete all stages?
                            when did the run happen?
                            one row per record showing stage completion.

2. Record Journey         — select one record by correlation ID.
                            see the full timeline: agent -> event -> timestamp -> payload.
                            correlation ID shown at the top, consistent throughout.

3. Batch Insights         — aggregate charts from fixture analytics data:
                            top skills, seniority distribution, role distribution,
                            locations, skill type distribution, quality/spam scores.

Data source: agents/data/output/pipeline_run.json
             Run `python agents/pipeline_runner.py` to generate it.

Usage:
    streamlit run agents/dashboard/streamlit_app.py

Design note (Week 2): Page 3 uses fixture data from the Analytics Agent.
In Week 7 when the Analytics Agent is real, Page 3 will reflect actual
extracted and aggregated data automatically — no dashboard code changes needed.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent.parent   # agents/
_RUN_LOG_PATH = _HERE / "data" / "output" / "pipeline_run.json"

# The canonical agent order — used for sorting the journey timeline.
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
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data
def load_run_log() -> list[dict]:
    """Load pipeline_run.json.  Returns an empty list if not found."""
    if not _RUN_LOG_PATH.exists():
        return []
    return json.loads(_RUN_LOG_PATH.read_text(encoding="utf-8"))


def build_record_map(entries: list[dict]) -> dict[str, list[dict]]:
    """Group log entries by correlation_id -> preserves insertion order."""
    record_map: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        cid = entry.get("correlation_id", "unknown")
        record_map[cid].append(entry)
    return dict(record_map)


def sort_key(cid: str) -> int:
    """Sort correlation IDs numerically when they are digit strings."""
    return int(cid) if cid.isdigit() else 0


# ---------------------------------------------------------------------------
# Page 1 — Pipeline Run Summary
# ---------------------------------------------------------------------------

def page_run_summary(entries: list[dict]) -> None:
    st.title("Pipeline Run Summary")

    if not entries:
        st.error(
            f"No run log found at `{_RUN_LOG_PATH}`.  \n"
            "Run the pipeline first:  \n"
            "```\npython agents/pipeline_runner.py\n```"
        )
        return

    record_map = build_record_map(entries)
    phase1_agents = [a for a in _AGENT_ORDER if a != "demand-analysis-agent"]

    # -- Headline metrics
    timestamps = [e["timestamp"] for e in entries if "timestamp" in e]
    run_start = min(timestamps) if timestamps else "—"
    run_end   = max(timestamps) if timestamps else "—"

    # Compute duration from earliest to latest timestamp.
    duration_str = "—"
    if run_start != "—" and run_end != "—":
        from datetime import datetime

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

    # -- Completion table
    st.subheader("Completion Table")
    st.caption(
        "One row per job record.  Each column is one pipeline stage.  "
        "Pass = event logged   Fail = stage missing or skipped"
    )

    rows = []
    for cid in sorted(record_map.keys(), key=sort_key):
        record_entries = record_map[cid]
        completed_agents = {e["agent_id"] for e in record_entries}

        # Pull a human-readable label from the first entry that has title/company.
        title, company = "—", "—"
        for e in record_entries:
            p = e.get("payload", {})
            if not title or title == "—":
                title = p.get("title") or title
            if not company or company == "—":
                company = p.get("company") or company
            if title != "—" and company != "—":
                break

        row: dict = {
            "Correlation ID": cid,
            "Title": title,
            "Company": company,
        }

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
        st.warning(
            f"{complete_count} / {total_count} records completed all Phase 1 stages."
        )


# ---------------------------------------------------------------------------
# Page 2 — Record Journey
# ---------------------------------------------------------------------------

def page_record_journey(entries: list[dict]) -> None:
    st.title("Record Journey")

    if not entries:
        st.error(
            f"No run log found at `{_RUN_LOG_PATH}`.  \n"
            "Run the pipeline first:  \n"
            "```\npython agents/pipeline_runner.py\n```"
        )
        return

    record_map = build_record_map(entries)

    # -- Record selector
    def label(cid: str) -> str:
        for e in record_map.get(cid, []):
            p = e.get("payload", {})
            t = p.get("title")
            c = p.get("company")
            if t and c:
                return f"[{cid}]  {t}  @  {c}"
        return f"Record {cid}"

    sorted_cids = sorted(record_map.keys(), key=sort_key)
    labels      = [label(cid) for cid in sorted_cids]
    label_to_cid = dict(zip(labels, sorted_cids, strict=True))

    selected_label = st.selectbox("Select a record to trace", labels)
    selected_cid   = label_to_cid[selected_label]

    st.markdown("---")

    # -- Header
    st.subheader(f"Correlation ID: `{selected_cid}`")
    st.caption(
        "This ID is set once when the record enters the pipeline and carried "
        "unchanged through all eight stages.  It is how you find a specific "
        "record in any log, at any stage, at any time."
    )

    # -- Timeline
    record_entries = sorted(
        record_map[selected_cid],
        key=lambda e: _AGENT_ORDER_INDEX.get(e.get("agent_id", ""), 99),
    )

    st.markdown("#### Stage-by-stage timeline")

    for entry in record_entries:
        agent_id   = entry.get("agent_id", "—")
        payload    = entry.get("payload", {})
        event_type = payload.get("event_type", agent_id)
        timestamp  = entry.get("timestamp", "—")
        is_phase2  = event_type == "Phase2Skipped"

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

            # Payload summary — show the most useful fields prominently.
            summary_fields = [
                "event_type", "posting_id", "title", "company",
                "seniority", "role_classification",
                "quality_score", "spam_score", "is_spam",
                "normalization_status", "extraction_status",
                "enrichment_status", "render_status", "pipeline_stage",
                "run_id", "total_postings",
            ]
            summary = {k: payload[k] for k in summary_fields if k in payload}
            if summary:
                st.markdown("**Payload summary**")
                st.json(summary)

            # Skills table (if present).
            skills = payload.get("skills")
            if skills:
                st.markdown("**Skills extracted**")
                st.dataframe(
                    pd.DataFrame(skills),
                    use_container_width=True,
                    hide_index=True,
                )

            # Top skills in analytics payload.
            top_skills = payload.get("top_skills")
            if top_skills:
                st.markdown("**Batch top skills** (from fixture analytics)")
                st.dataframe(
                    pd.DataFrame(top_skills),
                    use_container_width=True,
                    hide_index=True,
                )


# ---------------------------------------------------------------------------
# Page 3 — Batch Insights
# ---------------------------------------------------------------------------

def page_batch_insights(entries: list[dict]) -> None:
    st.title("Batch Insights")
    st.caption(
        "Aggregate view across all 10 job postings.  "
        "In Week 2, charts are drawn from the Analytics Agent fixture data.  "
        "In Week 7, they will reflect real extracted and aggregated data — "
        "no dashboard changes needed."
    )

    if not entries:
        st.error(
            f"No run log found at `{_RUN_LOG_PATH}`.  \n"
            "Run the pipeline first:  \n"
            "```\npython agents/pipeline_runner.py\n```"
        )
        return

    # Pull analytics payload from the first analytics-agent entry.
    analytics_entries = [e for e in entries if e.get("agent_id") == "analytics-agent"]
    if not analytics_entries:
        st.warning("No Analytics Agent entries found in the run log.")
        return

    p = analytics_entries[0].get("payload", {})

    # -- Top Skills bar chart
    st.subheader("Top Skills")
    top_skills = p.get("top_skills", [])
    if top_skills:
        df_skills = (
            pd.DataFrame(top_skills)
            .sort_values("count", ascending=False)
            .set_index("skill")
        )
        st.bar_chart(df_skills["count"])
    else:
        st.info("No top_skills data in analytics payload.")

    st.markdown("---")

    # -- Seniority distribution
    st.subheader("Seniority Distribution")
    seniority = p.get("seniority_distribution", {})
    if seniority:
        df_sen = (
            pd.DataFrame.from_dict(seniority, orient="index", columns=["count"])
            .reindex(["junior", "mid", "senior", "lead"])
            .dropna()
        )
        st.bar_chart(df_sen["count"])
    else:
        st.info("No seniority_distribution data.")

    st.markdown("---")

    # -- Role distribution  +  Locations  (side by side)
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
        else:
            st.info("No role_distribution data.")

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
        else:
            st.info("No locations data.")

    st.markdown("---")

    # -- Sectors
    st.subheader("Sectors")
    sectors = p.get("sectors", {})
    if sectors:
        df_sec = (
            pd.DataFrame.from_dict(sectors, orient="index", columns=["count"])
            .reset_index()
            .rename(columns={"index": "sector"})
            .sort_values("count", ascending=False)
        )
        st.dataframe(df_sec, use_container_width=True, hide_index=True)

    st.markdown("---")

    # -- Skill type distribution
    st.subheader("Skill Type Distribution")
    skill_types = p.get("skill_type_distribution", {})
    if skill_types:
        df_types = (
            pd.DataFrame.from_dict(skill_types, orient="index", columns=["count"])
            .reset_index()
            .rename(columns={"index": "type"})
        )
        st.bar_chart(df_types.set_index("type")["count"])
    else:
        st.info("No skill_type_distribution data.")

    st.markdown("---")

    # -- Quality & spam scores
    st.subheader("Quality & Spam Scores")
    col3, col4 = st.columns(2)

    avg_quality = p.get("avg_quality_score")
    avg_spam    = p.get("avg_spam_score")

    if avg_quality is not None:
        col3.metric(
            "Average Quality Score",
            f"{avg_quality:.3f}",
            help="1.0 = perfect completeness, clarity, and coherence",
        )
    if avg_spam is not None:
        col4.metric(
            "Average Spam Score",
            f"{avg_spam:.3f}",
            help="< 0.70 -> proceed  |  0.70-0.90 -> flag  |  > 0.90 -> reject",
        )

    # Per-record quality breakdown from enrichment entries.
    st.markdown("#### Per-record quality breakdown")
    enrichment_entries = [e for e in entries if e.get("agent_id") == "enrichment-agent"]
    if enrichment_entries:
        quality_rows = []
        for e in enrichment_entries:
            ep = e.get("payload", {})
            quality_rows.append({
                "Posting ID":  ep.get("posting_id"),
                "Title":       ep.get("title"),
                "Company":     ep.get("company"),
                "Role":        ep.get("role_classification"),
                "Seniority":   ep.get("seniority"),
                "Quality":     ep.get("quality_score"),
                "Spam":        ep.get("spam_score"),
                "Is Spam":     ep.get("is_spam"),
            })
        df_quality = pd.DataFrame(quality_rows).sort_values("Posting ID")
        st.dataframe(df_quality, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="JIE Journey Dashboard — Week 2",
        page_icon="*",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.title("JIE Dashboard")
    st.sidebar.caption("Week 2 — Walking Skeleton")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigate",
        options=[
            "Pipeline Run Summary",
            "Record Journey",
            "Batch Insights",
        ],
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"Data source:  \n`{_RUN_LOG_PATH.name}`"
    )

    if not _RUN_LOG_PATH.exists():
        st.sidebar.error("Run log not found.  Run the pipeline first.")

    entries = load_run_log()

    if page == "Pipeline Run Summary":
        page_run_summary(entries)
    elif page == "Record Journey":
        page_record_journey(entries)
    elif page == "Batch Insights":
        page_batch_insights(entries)


if __name__ == "__main__":
    main()
