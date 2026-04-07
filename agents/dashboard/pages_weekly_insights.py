"""Weekly Insights — analytics aggregate charts (Week 7 / issue #178)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import plotly.express as px
import streamlit as st

from agents.dashboard.pages_observability import _staleness_banner
from agents.dashboard.weekly_insights_queries import (
    fetch_skill_demand_weekly_availability,
    fetch_top_skills_for_week,
    max_computed_at,
)


def _staleness_banner_computed_at(computed_at: datetime | None) -> None:
    """Warn when aggregate ``computed_at`` is older than 24 hours (IMP-021 guideline)."""
    if computed_at is None:
        return
    if computed_at.tzinfo is None:
        computed_at = computed_at.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - computed_at
    if age > timedelta(hours=24):
        hrs = max(1, int(age.total_seconds() // 3600))
        st.warning(f"Skill demand aggregates may be stale (last computed ~{hrs} hours ago).")


def render_weekly_insights() -> None:
    st.title("Weekly Insights")
    st.caption(
        "Analytics aggregates by ISO week (Monday start). Charts refresh from PostgreSQL read-only; "
        "run the Analytics agent to populate `skill_demand_weekly`."
    )

    avail = fetch_skill_demand_weekly_availability()

    if not avail.ok:
        st.error(f"Could not reach the database: {avail.error}")
        st.info(
            "Check `PYTHON_DATABASE_URL` or `PYTHON_DATABASE_URL_READONLY` in `.env` and that "
            "PostgreSQL is running."
        )
        return

    _staleness_banner(avail.fetched_at)

    if not avail.table_exists:
        st.info(
            "The **`dbo.skill_demand_weekly`** table is not present yet. "
            "Apply agent migrations and run the Analytics aggregate refresh for your target week."
        )
        return

    if not avail.week_starts:
        st.warning("**`dbo.skill_demand_weekly` exists but has no rows yet.**")
        st.info(
            "The table is ready, but no weekly aggregates have been written. Typical next steps:\n\n"
            "1. Ensure jobs are ingested, normalized, enriched, and promoted where your analytics SQL expects them.\n"
            "2. Run the Analytics agent (or your Week 7 aggregate refresh) for a **Monday `week_start`** anchor.\n"
            "3. Re-open this page after refresh — the week dropdown appears once at least one `week_start` is present."
        )
        return

    week_options = list(avail.week_starts)
    labels = [d.isoformat() for d in week_options]

    selected_label = st.selectbox(
        "Week (Monday start)",
        options=labels,
        index=0,
        key="weekly_insights_week_start",
        help="Distinct `week_start` values from `skill_demand_weekly` (newest first).",
    )

    err, skills_df = fetch_top_skills_for_week(selected_label)
    if err:
        st.warning(f"Could not load skills for this week: {err}")
        return

    if skills_df.empty:
        st.warning(
            f"No skill rows found for **week_start = {selected_label}**, even though that week appears in the list."
        )
        st.info(
            "This usually means data changed since the week list was cached, the refresh wrote no skills for that "
            "anchor, or rows were removed. Try another week, rerun the app from the Streamlit menu, or re-run the "
            "analytics aggregate step for that `week_start`."
        )
        return

    st.subheader("Top 20 skills by posting count")
    _staleness_banner_computed_at(max_computed_at(skills_df))

    plot_df = skills_df.sort_values("posting_count", ascending=True)
    fig = px.bar(
        plot_df,
        x="posting_count",
        y="skill_label",
        orientation="h",
        labels={
            "posting_count": "Postings",
            "skill_label": "Skill",
        },
    )
    fig.update_layout(
        margin=dict(t=30, b=40, l=20, r=20),
        yaxis={"categoryorder": "total ascending"},
        height=max(400, 28 * len(plot_df)),
    )
    st.plotly_chart(fig, width="stretch")

    with st.expander("Underlying rows (top 20)"):
        st.dataframe(skills_df, width="stretch", hide_index=True)
