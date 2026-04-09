"""Weekly Insights — analytics aggregate charts (Week 7 / issue #178).

Layout: report week (selector) → Pair A sections (skills, velocity, co-occurrence) → cross-pair
placeholders. To add a table: implement ``fetch_*`` in ``weekly_insights_queries`` and append a
``_section_*`` block after the divider, using :func:`_section_has_data` for hints/empty states.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from agents.dashboard.pages_observability import _staleness_banner
from agents.dashboard.weekly_insights_queries import (
    fetch_insight_summary_placeholder,
    fetch_posting_freshness_placeholder,
    fetch_role_snapshot_weekly_placeholder,
    fetch_skill_co_occurrence_for_week,
    fetch_skill_demand_weekly_availability,
    fetch_skill_demand_weekly_history_for_skills,
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


def _section_has_data(
    load_hint: str | None,
    df: pd.DataFrame,
    *,
    title: str,
    empty_detail: str,
) -> bool:
    """Show warning (missing table / SQL) or consistent empty info; return True if ``df`` has rows."""
    if load_hint:
        st.warning(load_hint)
        return False
    if df.empty:
        st.info(f"**{title}** — {empty_detail}")
        return False
    return True


def _velocity_sparkline_skill_key(skill_label: object, esco_uri: object) -> tuple[str, str | None]:
    """Normalize velocity row keys for SQL history lookup (NULL-safe ``esco_uri``)."""
    label = str(skill_label).strip()
    if esco_uri is None or (isinstance(esco_uri, float) and pd.isna(esco_uri)):
        return (label, None)
    text = str(esco_uri).strip()
    return (label, text if text else None)


def _layout_weekly_horizontal_bar(
    fig: go.Figure,
    *,
    row_count: int,
    row_px: int = 24,
    base_px: int = 320,
    top_margin: int = 40,
    bottom_margin: int = 40,
) -> None:
    """Shared margins/height for horizontal bar charts on this page."""
    fig.update_layout(
        margin=dict(t=top_margin, b=bottom_margin, l=20, r=20),
        yaxis={"categoryorder": "total ascending"},
        height=max(base_px, row_px * max(1, row_count)),
    )


def _render_report_week_selector(labels: list[str]) -> str:
    """Single week control at the top of the page."""
    st.subheader("Report week")
    st.caption(
        "Monday-aligned `week_start` values from **`dbo.skill_demand_weekly`** (newest first). "
        "Other sections use this anchor when their aggregate table exposes the same week column."
    )
    choice = st.selectbox(
        "Week",
        options=labels,
        index=0,
        key="weekly_insights_week_start",
        help="Drives week-scoped queries below.",
    )
    st.divider()
    return choice


def render_weekly_insights() -> None:
    st.title("Weekly Insights")
    st.caption(
        "Analytics aggregates by ISO week. Read-only PostgreSQL; populate via the Analytics agent "
        "(Pair A–D: skills, velocity, co-occurrence, roles, freshness, summaries, …)."
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
            "**Report week** — `dbo.skill_demand_weekly` is not present yet. "
            "Apply agent migrations and run the Analytics aggregate refresh for your target week."
        )
        return

    if not avail.week_starts:
        st.warning("**Report week** — `skill_demand_weekly` exists but has no `week_start` rows yet.")
        st.info(
            "**Next steps** — Ingest and enrich jobs, then run the Week 7 aggregate refresh for a Monday "
            "`week_start`. The week dropdown appears after at least one distinct week is stored."
        )
        return

    labels = [d.isoformat() for d in avail.week_starts]
    selected_label = _render_report_week_selector(labels)

    err, skills_df = fetch_top_skills_for_week(selected_label)
    if err:
        st.warning(f"**Top skills** — could not load: {err}")
        return

    if skills_df.empty:
        st.warning(
            f"**Top skills** — no rows for **week_start = {selected_label}** though this week is listed."
        )
        st.info(
            "**Next steps** — Rerun the app, pick another week, or re-run the skill-demand aggregate for "
            "this anchor (data may have changed under cache)."
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
    _layout_weekly_horizontal_bar(fig, row_count=len(plot_df), row_px=28, base_px=400, top_margin=30)
    st.plotly_chart(fig, width="stretch")

    with st.expander("Underlying rows (top 20)"):
        st.dataframe(skills_df, width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("Skill velocity")
    st.caption(
        "**`dbo.skill_velocity`** (step 8): demand, smoothed week-over-week change, IMP-021 trend label, "
        "confidence. Sparklines use **`dbo.skill_demand_weekly`** posting counts for the same skills (newest "
        "weeks ending at the selected anchor)."
    )

    vel_hint, vel_df = fetch_skill_velocity_for_week(selected_label)
    if _section_has_data(
        vel_hint,
        vel_df,
        title="Skill velocity",
        empty_detail=(
            f"No rows for **week = {selected_label}**. Run the velocity refresh after `skill_demand_weekly` "
            "has history for this anchor."
        ),
    ):
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
        _layout_weekly_horizontal_bar(fig_v, row_count=len(bar_src))
        st.plotly_chart(fig_v, width="stretch")

        sparkline_n = 8
        history_weeks = 8
        spark_slice = vel_df.head(sparkline_n)
        skills_key = tuple(
            _velocity_sparkline_skill_key(r["skill_label"], r["esco_uri"]) for _, r in spark_slice.iterrows()
        )
        hist_err, hist_df = fetch_skill_demand_weekly_history_for_skills(
            selected_label,
            skills_key,
            max_weeks=history_weeks,
        )
        if hist_err:
            st.caption(f"Demand history for sparklines could not load: {hist_err}")
        elif hist_df.empty:
            st.caption(
                "No matching **`skill_demand_weekly`** rows for these velocity skills in the recent window."
            )
        else:
            n_weeks = hist_df["week_start"].nunique()
            if n_weeks < 2:
                st.caption(
                    f"Sparklines need at least two distinct `week_start` values in the last **{history_weeks}** "
                    f"weeks; found **{n_weeks}**."
                )
            else:
                spark_slice = spark_slice.reset_index(drop=True)
                spark_slice["_uri_norm"] = spark_slice["esco_uri"].apply(
                    lambda u: None
                    if u is None or (isinstance(u, float) and pd.isna(u)) or str(u).strip() == ""
                    else str(u).strip()
                )
                hist_work = hist_df.copy()
                hist_work["_uri_norm"] = hist_work["esco_uri"].apply(
                    lambda u: None
                    if u is None or (isinstance(u, float) and pd.isna(u)) or str(u).strip() == ""
                    else str(u).strip()
                )
                merged = spark_slice.merge(
                    hist_work,
                    left_on=["skill_label", "_uri_norm"],
                    right_on=["skill_label", "_uri_norm"],
                    how="inner",
                    suffixes=("", "_h"),
                )
                merged["week_start"] = pd.to_datetime(merged["week_start"])
                order = []
                seen: set[str] = set()
                for _, r in spark_slice.iterrows():
                    lbl = str(r["skill_label"])
                    u = r["_uri_norm"]
                    key = f"{lbl}\0{u or ''}"
                    if key in seen:
                        continue
                    seen.add(key)
                    order.append(lbl + ("" if not u else f" ({u[:28]}…)" if len(u) > 28 else f" ({u})"))
                merged["display_skill"] = merged.apply(
                    lambda r: str(r["skill_label"])
                    + (
                        ""
                        if r["_uri_norm"] is None
                        else (
                            f" ({r['_uri_norm'][:28]}…)"
                            if len(r["_uri_norm"]) > 28
                            else f" ({r['_uri_norm']})"
                        )
                    ),
                    axis=1,
                )
                present = set(merged["display_skill"].unique())
                order = [o for o in order if o in present]
                if merged.empty or not order:
                    st.caption(
                        "Demand history returned rows, but none matched these velocity skills "
                        "(check `skill_label` / `esco_uri` alignment between step 2 and step 8)."
                    )
                else:
                    n_facets = merged["display_skill"].nunique()
                    fig_sp = px.line(
                        merged,
                        x="week_start",
                        y="posting_count",
                        facet_row="display_skill",
                        markers=True,
                        labels={
                            "week_start": "Week",
                            "posting_count": "Postings",
                            "display_skill": "Skill",
                        },
                        title=f"Weekly demand ({n_facets} skills, |WoW| table order)",
                        category_orders={"display_skill": order},
                    )
                    row_h = 52
                    fig_sp.update_layout(
                        height=max(220, row_h * n_facets + 80),
                        margin=dict(t=50, b=40, l=20, r=20),
                        showlegend=False,
                    )
                    fig_sp.update_yaxes(matches=None, title_text="")
                    fig_sp.update_xaxes(title_text="")

                    def _facet_short_ann(a: go.layout.Annotation) -> None:
                        if "=" in (a.text or ""):
                            a.update(text=a.text.split("=", 1)[-1])

                    fig_sp.for_each_annotation(_facet_short_ann)
                    st.plotly_chart(fig_sp, width="stretch")

        with st.expander("Raw `skill_velocity` rows (same query order)"):
            st.dataframe(vel_df, width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("Skill co-occurrence")
    st.caption(
        "**`dbo.skill_co_occurrence`** (step 9): skills that co-occur on postings (lexicographic pairs per "
        "IMP-021). Heatmaps can be added later."
    )

    co_hint, co_df = fetch_skill_co_occurrence_for_week(selected_label)
    if _section_has_data(
        co_hint,
        co_df,
        title="Skill co-occurrence",
        empty_detail=(
            f"No pairs for **week_start = {selected_label}**. Run the co-occurrence refresh (step 9) once "
            "weekly skill demand exists for this week."
        ),
    ):
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
        _layout_weekly_horizontal_bar(fig_co, row_count=len(co_bar), row_px=22)
        st.plotly_chart(fig_co, width="stretch")

        with st.expander("Raw `skill_co_occurrence` rows (query order)"):
            st.dataframe(co_df, width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("Role salary snapshot")
    st.caption(
        "**`dbo.role_snapshot_weekly`** (Pair C — placeholder). "
        "Contract columns include **`canonical_role_id`**, **`role_title`**, **`salary_p25`** / **`median_salary`** / **`salary_p75`**. "
        f"Filtered to **week_start = {selected_label}**."
    )
    rs_hint, rs_df = fetch_role_snapshot_weekly_placeholder(selected_label)
    if _section_has_data(
        rs_hint,
        rs_df,
        title="Role salary snapshot",
        empty_detail=(
            f"No rows for **week_start = {selected_label}** (or table empty). Run Pair C role snapshot "
            "aggregates for this anchor."
        ),
    ):
        st.dataframe(rs_df, width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("Posting lifecycle")
    st.caption(
        "**`dbo.posting_freshness`** (Pair D — placeholder): per-posting lifecycle snapshot per "
        "`.cursor/rules/analytics-guardrails.mdc` (`duration_days`, `is_repost`, …); not a pre-aggregated bucket table."
    )
    pf_hint, pf_df = fetch_posting_freshness_placeholder()
    if _section_has_data(
        pf_hint,
        pf_df,
        title="Posting lifecycle",
        empty_detail="No per-posting freshness rows yet. Run the Pair D posting-freshness persistence when wired.",
    ):
        st.dataframe(pf_df, width="stretch", hide_index=True)
        if "duration_days" in pf_df.columns and not pf_df.empty:
            hist_df = pf_df.assign(
                _dd=pd.to_numeric(pf_df["duration_days"], errors="coerce")
            ).dropna(subset=["_dd"])
            if not hist_df.empty:
                fig_pf = px.histogram(
                    hist_df,
                    x="_dd",
                    labels={"_dd": "Duration (days listed)"},
                    title="Sample of postings by duration_days (latest rows)",
                )
                fig_pf.update_layout(margin=dict(t=40, b=60, l=40, r=20))
                st.plotly_chart(fig_pf, width="stretch")

    st.markdown("---")
    st.subheader("Weekly insight summary")
    st.caption(
        "**`dbo.insight_summary`** (Pair D). Placeholder uses the **latest** row; filter by selected week when "
        "the table exposes `week_start` (or equivalent)."
    )
    ins_hint, ins_df = fetch_insight_summary_placeholder()
    if _section_has_data(
        ins_hint,
        ins_df,
        title="Weekly insight summary",
        empty_detail="No summary rows yet. Wire the LLM/template writer (Pair D) to populate this table.",
    ):
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
