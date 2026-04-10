"""Week 6 observability pages: Ingestion Overview and Normalization Quality."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from agents.dashboard.observability_queries import (
    resolve_ingestion_obs,
    resolve_normalization_obs,
)


def _staleness_banner(fetched_at: datetime) -> None:
    """Warn when displayed data is older than the 5-minute cache window."""
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - fetched_at
    if age > timedelta(minutes=5):
        mins = max(1, int(age.total_seconds() // 60))
        st.warning(f"Data last updated ~{mins} minutes ago (target refresh: every 5 minutes).")


def render_ingestion_overview() -> None:
    st.title("Ingestion Overview")
    st.caption("Pipeline health: volumes, deduplication, and ingestion errors (read-only).")

    data, used_fallback, err_msg = resolve_ingestion_obs(st.session_state)

    if used_fallback and err_msg:
        st.warning(f"Showing last successful data. Current load failed: {err_msg}")
    elif err_msg and not used_fallback:
        st.error(f"Could not load ingestion data: {err_msg}")

    if data.schema_note:
        st.warning(data.schema_note)

    _staleness_banner(data.fetched_at)

    col1, col2, col3 = st.columns(3)
    dr = data.dedup_rate_pct
    er = data.error_rate_pct
    col1.metric(
        "Dedup hit rate",
        f"{dr:.1f} %" if dr is not None else "N/A",
        help="SUM(dedup_count) / SUM(staged_count + dedup_count) across all runs",
    )
    col2.metric(
        "Row-level error rate",
        f"{er:.1f} %" if er is not None else "N/A",
        help="SUM(error_count) / SUM(total_fetched) across all runs",
    )
    n_runs = len(data.runs_all_df) if data.runs_all_df is not None else 0
    col3.metric("Ingestion runs (total)", n_runs)

    st.markdown("---")
    st.subheader("Records ingested per day (UTC)")
    if data.daily_df.empty:
        st.info("No raw ingested records yet — run the Ingestion agent to populate data.")
    else:
        dfp = data.daily_df.copy()
        if "day" in dfp.columns:
            dfp["day"] = pd.to_datetime(dfp["day"]).dt.strftime("%Y-%m-%d")
        fig = px.bar(
            dfp,
            x="day",
            y="record_count",
            labels={"day": "Day (UTC)", "record_count": "Records"},
        )
        fig.update_layout(xaxis_tickangle=-45, margin=dict(t=30, b=80))
        st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    st.subheader("Recent ingestion runs (last 10)")
    if data.recent_runs_df.empty:
        st.info("No ingestion runs in the database yet.")
    else:
        display_cols = [
            c
            for c in [
                "run_id",
                "source",
                "status",
                "started_at",
                "total_fetched",
                "staged_count",
                "dedup_count",
                "error_count",
            ]
            if c in data.recent_runs_df.columns
        ]
        st.dataframe(
            data.recent_runs_df[display_cols],
            width="stretch",
            hide_index=True,
        )


def render_normalization_quality() -> None:
    st.title("Normalization Quality")
    st.caption("Schema conformance, quarantine reasons, and salary field coverage.")

    data, used_fallback, err_msg = resolve_normalization_obs(st.session_state)

    if used_fallback and err_msg:
        st.warning(f"Showing last successful data. Current load failed: {err_msg}")
    elif err_msg and not used_fallback:
        st.error(f"Could not load normalization data: {err_msg}")

    if data.schema_note:
        st.warning(data.schema_note)

    _staleness_banner(data.fetched_at)

    col1, col2, col3 = st.columns(3)
    cp = data.conformance_pct
    sp = data.salary_coverage_pct
    col1.metric(
        "Schema conformance",
        f"{cp:.1f} %" if cp is not None else "N/A",
        help="Share of normalized_jobs rows with normalization_status = 'success'",
    )
    col2.metric(
        "Salary coverage",
        f"{sp:.1f} %" if sp is not None else "N/A",
        help="Rows with salary_min, salary_max, or non-empty salary_raw",
    )
    col3.metric("Normalized rows", data.normalized_row_count)

    st.markdown("---")
    st.subheader("Conformance gauge")
    if cp is None:
        st.info("No normalized rows yet — conformance not applicable.")
    else:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=round(cp, 1),
                title={"text": "% passing schema (success status)"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 50], "color": "lightgray"},
                        {"range": [50, 80], "color": "gray"},
                        {"range": [80, 100], "color": "lightgreen"},
                    ],
                },
            )
        )
        fig.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    st.subheader("Quarantine breakdown")
    if data.quarantine_df.empty:
        st.info("No quarantined records — or normalization has not produced quarantine rows yet.")
    else:
        qdf = data.quarantine_df.copy()
        fig2 = px.bar(
            qdf,
            x="error_type",
            y="record_count",
            labels={"error_type": "Error type", "record_count": "Count"},
        )
        fig2.update_layout(xaxis_tickangle=-35, margin=dict(t=30, b=120))
        st.plotly_chart(fig2, width="stretch")
        st.dataframe(qdf, width="stretch", hide_index=True)
