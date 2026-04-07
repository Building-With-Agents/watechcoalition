"""Weekly Insights — analytics aggregate charts (Week 7 / issue #178)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

from agents.dashboard.pages_observability import _staleness_banner
from agents.dashboard.weekly_insights_queries import (
    fetch_insight_summary_placeholder,
    fetch_posting_freshness_placeholder,
    fetch_role_snapshot_weekly_placeholder,
    fetch_skill_co_occurrence_for_week,
    fetch_skill_demand_weekly_availability,
    fetch_skill_velocity_for_week,
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
        "Analytics aggregates by ISO week (Monday start). Read-only PostgreSQL; populate tables via the "
        "Analytics agent (Pair A–D aggregates: skills, velocity, co-occurrence, roles, freshness, summaries, …)."
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

    st.markdown("---")
    st.subheader("Skill velocity")
    st.caption(
        "From **`dbo.skill_velocity`** (analytics step 8): demand for the anchor week, week-over-week "
        "change on a smoothed series, IMP-021 trend label, and confidence. "
        "True multi-week sparklines can be added later from `skill_demand_weekly` history."
    )

    vel_hint, vel_df = fetch_skill_velocity_for_week(selected_label)
    if vel_hint:
        st.warning(vel_hint)
    elif vel_df.empty:
        st.info(
            f"No velocity rows for **week = {selected_label}**. "
            "Run the Analytics aggregate refresh for this anchor after `skill_demand_weekly` is populated "
            "(velocity depends on weekly demand history)."
        )
    else:
        display = vel_df.copy()
        display["wow_pct"] = (pd.to_numeric(display["week_over_week_change"], errors="coerce") * 100.0).map(
            lambda x: f"{x:+.1f} %" if pd.notna(x) else "—"
        )
        display["trend_confidence_fmt"] = pd.to_numeric(
            display["trend_confidence"], errors="coerce"
        ).map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
        show_cols = [
            "skill_label",
            "demand_count",
            "wow_pct",
            "four_week_trend",
            "trend_confidence_fmt",
        ]
        rename = {
            "skill_label": "Skill",
            "demand_count": "Demand (postings)",
            "wow_pct": "WoW change (est.)",
            "four_week_trend": "4w trend",
            "trend_confidence_fmt": "Trend confidence",
        }
        table_df = display[show_cols].rename(columns=rename)
        st.dataframe(table_df, width="stretch", hide_index=True)

        bar_cap = 15
        bar_src = vel_df.head(bar_cap).copy()
        bar_src["wow_pct_float"] = pd.to_numeric(bar_src["week_over_week_change"], errors="coerce") * 100.0
        bar_src = bar_src.sort_values("wow_pct_float", ascending=True)
        fig_v = px.bar(
            bar_src,
            x="wow_pct_float",
            y="skill_label",
            orientation="h",
            labels={
                "wow_pct_float": "Week-over-week change (%, smoothed series)",
                "skill_label": "Skill",
            },
            title=f"Largest |WoW| moves (top {bar_cap} by magnitude)",
        )
        fig_v.update_layout(
            margin=dict(t=40, b=40, l=20, r=20),
            yaxis={"categoryorder": "total ascending"},
            height=max(320, 24 * len(bar_src)),
        )
        st.plotly_chart(fig_v, width="stretch")

        with st.expander("Raw `skill_velocity` rows (same query order)"):
            st.dataframe(vel_df, width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("Skill co-occurrence")
    st.caption(
        "From **`dbo.skill_co_occurrence`** (analytics step 9): pairs of skills that appear together on "
        "postings in the week (lexicographic pair order per IMP-021). "
        "A full heatmap can be added later; this view lists the strongest pairs first."
    )

    co_hint, co_df = fetch_skill_co_occurrence_for_week(selected_label)
    if co_hint:
        st.warning(co_hint)
    elif co_df.empty:
        st.info(
            f"No co-occurrence rows for **week_start = {selected_label}**. "
            "Run the Analytics co-occurrence refresh (step 9) for this anchor once weekly skill demand exists."
        )
    else:
        co_display = co_df.copy()
        co_display["pair"] = co_display["skill_a"].astype(str) + " ↔ " + co_display["skill_b"].astype(str)
        st.dataframe(
            co_display[["pair", "co_occurrence_count"]].rename(
                columns={
                    "pair": "Skill pair",
                    "co_occurrence_count": "Co-postings",
                }
            ),
            width="stretch",
            hide_index=True,
        )

        co_bar_cap = 15
        co_bar = co_df.head(co_bar_cap).copy()
        co_bar["pair"] = co_bar["skill_a"].astype(str) + " ↔ " + co_bar["skill_b"].astype(str)
        co_bar = co_bar.sort_values("co_occurrence_count", ascending=True)
        fig_co = px.bar(
            co_bar,
            x="co_occurrence_count",
            y="pair",
            orientation="h",
            labels={
                "co_occurrence_count": "Co-posting count",
                "pair": "Skill pair",
            },
            title=f"Top {min(co_bar_cap, len(co_bar))} pairs by co-occurrence",
        )
        fig_co.update_layout(
            margin=dict(t=40, b=40, l=20, r=20),
            yaxis={"categoryorder": "total ascending"},
            height=max(320, 22 * len(co_bar)),
        )
        st.plotly_chart(fig_co, width="stretch")

        with st.expander("Raw `skill_co_occurrence` rows (query order)"):
            st.dataframe(co_df, width="stretch", hide_index=True)

    # --- Phase 3 cross-pair placeholders (swap queries in weekly_insights_queries when schema is final) ---
    st.markdown("---")
    st.subheader("Role salary snapshot")
    st.caption(
        "Cross-pair (**`dbo.role_snapshot_weekly`**, Pair C). Placeholder: tabular p25 / median / p75. "
        f"Filtered to **week_start = {selected_label}** when that column exists. "
        "Replace with box/violin plots once the schema is stable."
    )
    rs_hint, rs_df = fetch_role_snapshot_weekly_placeholder(selected_label)
    if rs_hint:
        st.warning(rs_hint)
    elif rs_df.empty:
        st.info(
            f"No role snapshot rows for **week_start = {selected_label}** (or table is empty). "
            "Pair C aggregates must run for this anchor before salary distributions appear."
        )
    else:
        st.dataframe(rs_df, width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("Posting lifecycle")
    st.caption(
        "Cross-pair (**`dbo.posting_freshness`**). Placeholder: bucket counts and average days listed "
        "(runbook shape). Week filtering can be added when the table carries `week_start`."
    )
    pf_hint, pf_df = fetch_posting_freshness_placeholder()
    if pf_hint:
        st.warning(pf_hint)
    elif pf_df.empty:
        st.info(
            "No posting freshness rows yet. Lifecycle metrics will populate after the analytics "
            "freshness aggregate is implemented and run."
        )
    else:
        st.dataframe(pf_df, width="stretch", hide_index=True)
        if "freshness_bucket" in pf_df.columns and "posting_count" in pf_df.columns:
            pf_chart = pf_df
            if "avg_days_listed" in pf_df.columns:
                pf_chart = pf_df.sort_values(
                    "avg_days_listed",
                    ascending=True,
                    na_position="last",
                )
            fig_pf = px.bar(
                pf_chart,
                x="freshness_bucket",
                y="posting_count",
                labels={
                    "freshness_bucket": "Freshness bucket",
                    "posting_count": "Postings",
                },
                title="Postings by freshness bucket",
            )
            fig_pf.update_layout(margin=dict(t=40, b=80, l=40, r=20), xaxis_tickangle=-30)
            st.plotly_chart(fig_pf, width="stretch")

    st.markdown("---")
    st.subheader("Weekly insight summary")
    st.caption(
        "Cross-pair (**`dbo.insight_summary`**, Pair D). Shows the **latest** row only in this placeholder; "
        "tie to the selected week when `week_start` (or equivalent) exists on the table."
    )
    ins_hint, ins_df = fetch_insight_summary_placeholder()
    if ins_hint:
        st.warning(ins_hint)
    elif ins_df.empty:
        st.info(
            "No insight summary rows yet. After Pair D wires the LLM/template writer, "
            "`is_llm_generated` and `summary_type` will appear here."
        )
    else:
        row = ins_df.iloc[0]
        raw_flag = row.get("is_llm_generated")
        is_llm = raw_flag is True or str(raw_flag).lower() in ("true", "1", "t")
        source_label = "LLM-generated" if is_llm else "Template / deterministic"
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Summary source", source_label)
        col_b.metric("Type", str(row.get("summary_type") or "—"))
        created = row.get("created_at")
        col_c.metric("Created", str(created)[:19] if created is not None else "—")
        body = row.get("summary_text") or ""
        with st.expander("Summary text"):
            if body:
                st.markdown(str(body))
            else:
                st.caption("Empty `summary_text` for this row.")
