"""Cached read-only queries for the Weekly Insights dashboard (Week 7 / issue #178)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from agents.dashboard.readonly_engine import get_dashboard_engine
from agents.dashboard.relation_safe import read_sql_relation_safe

_SKILL_DEMAND_TABLE = "skill_demand_weekly"

# ---------------------------------------------------------------------------
# Cross-pair sections — placeholder / fallback SQL until Pair C/D tables are populated.
# CONTRACT refs: .cursor/rules/canonical-role-clustering.mdc (role_snapshot_weekly),
# .cursor/rules/analytics-guardrails.mdc (posting_freshness per-posting shape).
# ---------------------------------------------------------------------------


def _read_cross_pair_sql(
    sql: str,
    *,
    params: dict[str, Any] | None,
    missing_table_hint: str,
) -> tuple[str | None, pd.DataFrame]:
    """``read_sql_relation_safe`` plus soft-fail on missing/renamed columns (ProgrammingError)."""
    engine = get_dashboard_engine()
    try:
        df, hint = read_sql_relation_safe(
            sql,
            engine,
            params=params,
            user_hint=missing_table_hint,
        )
        if hint:
            return hint, df
        return None, df
    except Exception as exc:
        msg = str(exc).lower()
        if "does not exist" in msg:
            return (
                "Cross-pair query failed (table or column missing / renamed). "
                "Adjust the SQL in `fetch_role_snapshot_weekly_placeholder`, "
                "`fetch_posting_freshness_placeholder`, or `fetch_insight_summary_placeholder` "
                "when Pair C/D schema lands.",
                pd.DataFrame(),
            )
        raise


def _to_date(value: Any) -> date:
    """Normalize pandas/DB week values to ``date`` for selectbox keys."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if hasattr(value, "date") and callable(value.date):
        d = value.date()
        if isinstance(d, date) and not isinstance(d, datetime):
            return d
    return pd.Timestamp(value).date()


@dataclass(frozen=True)
class SkillDemandWeeklyAvailability:
    """Whether ``dbo.skill_demand_weekly`` exists and which week anchors have rows."""

    fetched_at: datetime
    ok: bool
    error: str | None
    table_exists: bool
    week_starts: tuple[date, ...]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_skill_demand_weekly_availability() -> SkillDemandWeeklyAvailability:
    """Detect table presence and distinct ``week_start`` values (newest first)."""
    ts = datetime.now(timezone.utc)
    try:
        engine = get_dashboard_engine()
        # Table name is a module constant (not user input).
        exists_sql = f"""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'dbo'
                  AND table_name = '{_SKILL_DEMAND_TABLE}'
            ) AS exists
        """
        row = pd.read_sql(exists_sql, engine)
        exists = bool(row.iloc[0]["exists"]) if not row.empty else False
        if not exists:
            return SkillDemandWeeklyAvailability(
                fetched_at=ts,
                ok=True,
                error=None,
                table_exists=False,
                week_starts=(),
            )
        weeks_sql = """
            SELECT DISTINCT week_start
            FROM dbo.skill_demand_weekly
            ORDER BY week_start DESC
        """
        weeks_df = pd.read_sql(weeks_sql, engine)
        if weeks_df.empty:
            return SkillDemandWeeklyAvailability(
                fetched_at=ts,
                ok=True,
                error=None,
                table_exists=True,
                week_starts=(),
            )
        raw_weeks = [_to_date(x) for x in weeks_df["week_start"].tolist()]
        return SkillDemandWeeklyAvailability(
            fetched_at=ts,
            ok=True,
            error=None,
            table_exists=True,
            week_starts=tuple(raw_weeks),
        )
    except Exception as exc:
        return SkillDemandWeeklyAvailability(
            fetched_at=ts,
            ok=False,
            error=str(exc),
            table_exists=False,
            week_starts=(),
        )


@st.cache_data(ttl=300, show_spinner=False)
def fetch_top_skills_for_week(week_start_iso: str) -> tuple[str | None, pd.DataFrame]:
    """Top 20 skills by ``posting_count`` for a single ``week_start``.

    Returns ``(error_message, dataframe)``. On success, ``error_message`` is ``None``.
    Columns: ``skill_label``, ``esco_uri``, ``posting_count``, ``employer_count``, ``computed_at``.
    """
    try:
        engine = get_dashboard_engine()
        sql = """
            SELECT skill_label,
                   esco_uri,
                   posting_count,
                   employer_count,
                   computed_at
            FROM dbo.skill_demand_weekly
            WHERE week_start = CAST(%(ws)s AS date)
            ORDER BY posting_count DESC
            LIMIT 20
        """
        df = pd.read_sql(sql, engine, params={"ws": week_start_iso})
        return None, df
    except Exception as exc:
        return str(exc), pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_skill_velocity_for_week(week_start_iso: str) -> tuple[str | None, pd.DataFrame]:
    """Load ``dbo.skill_velocity`` for the analytics anchor week (DB column ``week``).

    Returns ``(user_facing_error_or_missing_table_hint, dataframe)``. On full success the first
    value is ``None``. Columns match the repo ORM: ``skill_label``, ``esco_uri``, ``week``,
    ``demand_count``, ``week_over_week_change``, ``four_week_trend``, ``trend_confidence``.
    Rows are ordered by largest absolute week-over-week move first (up to 100 rows).
    """
    engine = get_dashboard_engine()
    sql = """
        SELECT skill_label,
               esco_uri,
               week,
               demand_count,
               week_over_week_change,
               four_week_trend,
               trend_confidence
        FROM dbo.skill_velocity
        WHERE week = CAST(%(ws)s AS date)
        ORDER BY ABS(week_over_week_change) DESC
        LIMIT 100
    """
    df, hint = read_sql_relation_safe(
        sql,
        engine,
        params={"ws": week_start_iso},
        user_hint=(
            "`dbo.skill_velocity` is missing. Apply migrations and run the Analytics velocity refresh "
            "(step 8) after `skill_demand_weekly` is populated."
        ),
    )
    if hint:
        return hint, df
    return None, df


@st.cache_data(ttl=300, show_spinner=False)
def fetch_skill_demand_weekly_history_for_skills(
    week_start_iso: str,
    skills_key: tuple[tuple[str, str | None], ...],
    *,
    max_weeks: int = 8,
) -> tuple[str | None, pd.DataFrame]:
    """``posting_count`` time series from ``dbo.skill_demand_weekly`` for fixed skills up to anchor week.

    ``skills_key`` is an ordered, hashable sequence of ``(skill_label, esco_uri)`` pairs (``esco_uri``
    ``None`` matches SQL NULL via ``IS NOT DISTINCT FROM``). Weeks are the **latest** ``max_weeks``
    distinct ``week_start`` values in the table on or before ``week_start_iso`` (newest-first cap).

    Returns ``(error_message, dataframe)`` like :func:`fetch_top_skills_for_week` on failure.
    Columns: ``week_start``, ``skill_label``, ``esco_uri``, ``posting_count``.
    """
    if not skills_key:
        return None, pd.DataFrame()
    try:
        engine = get_dashboard_engine()
        or_parts: list[str] = []
        params: dict[str, Any] = {
            "ws_end": week_start_iso,
            "max_weeks": int(max_weeks),
        }
        for i, (label, esco_uri) in enumerate(skills_key):
            or_parts.append(f"(s.skill_label = %(lbl{i})s AND s.esco_uri IS NOT DISTINCT FROM %(esc{i})s)")
            params[f"lbl{i}"] = label
            params[f"esc{i}"] = esco_uri
        where_skills = " OR ".join(or_parts)
        sql = f"""
            SELECT s.week_start, s.skill_label, s.esco_uri, s.posting_count
            FROM dbo.skill_demand_weekly s
            WHERE s.week_start IN (
                SELECT week_start FROM (
                    SELECT DISTINCT week_start
                    FROM dbo.skill_demand_weekly
                    WHERE week_start <= CAST(%(ws_end)s AS date)
                    ORDER BY week_start DESC
                    LIMIT %(max_weeks)s
                ) w
            )
            AND ({where_skills})
            ORDER BY s.week_start ASC, s.skill_label ASC, s.esco_uri ASC NULLS FIRST
        """
        df = pd.read_sql(sql, engine, params=params)
        return None, df
    except Exception as exc:
        return str(exc), pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_skill_co_occurrence_for_week(week_start_iso: str) -> tuple[str | None, pd.DataFrame]:
    """Load ``dbo.skill_co_occurrence`` for ``week_start`` (analytics step 9).

    Returns ``(missing_table_hint, dataframe)`` with success as ``(None, df)``.
    Columns: ``skill_a``, ``skill_b``, ``co_occurrence_count``, ``week_start``, ``computed_at``.
    Rows are ordered by co-occurrence count descending (up to 200; cap matches typical persist size).
    """
    engine = get_dashboard_engine()
    sql = """
        SELECT skill_a,
               skill_b,
               co_occurrence_count,
               week_start,
               computed_at
        FROM dbo.skill_co_occurrence
        WHERE week_start = CAST(%(ws)s AS date)
        ORDER BY co_occurrence_count DESC
        LIMIT 200
    """
    df, hint = read_sql_relation_safe(
        sql,
        engine,
        params={"ws": week_start_iso},
        user_hint=(
            "`dbo.skill_co_occurrence` is missing. Apply migrations and run the Analytics co-occurrence "
            "refresh (step 9) after `skill_demand_weekly` is populated for that week."
        ),
    )
    if hint:
        return hint, df
    return None, df


@st.cache_data(ttl=300, show_spinner=False)
def fetch_role_snapshot_weekly_placeholder(week_start_iso: str) -> tuple[str | None, pd.DataFrame]:
    """Pair C — ``dbo.role_snapshot_weekly`` for the selected week (placeholder / fallback).

    Column names per ``.cursor/rules/canonical-role-clustering.mdc``: ``canonical_role_id``,
    ``role_title``, ``posting_count``, ``median_salary``, ``salary_p25``, ``salary_p75``.
    """
    sql = """
        SELECT canonical_role_id,
               role_title,
               posting_count,
               median_salary,
               salary_p25,
               salary_p75
        FROM dbo.role_snapshot_weekly
        WHERE week_start = CAST(%(ws)s AS date)
        ORDER BY posting_count DESC
        LIMIT 30
    """
    return _read_cross_pair_sql(
        sql,
        params={"ws": week_start_iso},
        missing_table_hint=(
            "`dbo.role_snapshot_weekly` is not available yet (Pair C). "
            "Salary distribution charts will appear after migrations and the role snapshot refresh."
        ),
    )


@st.cache_data(ttl=300, show_spinner=False)
def fetch_posting_freshness_placeholder() -> tuple[str | None, pd.DataFrame]:
    """Pair D — per-posting ``dbo.posting_freshness`` rows (placeholder / fallback).

    Shape per ``.cursor/rules/analytics-guardrails.mdc`` — not a bucket aggregate table.
    """
    sql = """
        SELECT posting_id,
               first_seen,
               last_seen,
               duration_days,
               is_repost,
               repost_count,
               fill_proxy,
               computed_at
        FROM dbo.posting_freshness
        ORDER BY computed_at DESC NULLS LAST
        LIMIT 100
    """
    return _read_cross_pair_sql(
        sql,
        params=None,
        missing_table_hint=(
            "`dbo.posting_freshness` is not available yet (Pair D). "
            "Lifecycle rows appear after the analytics posting-freshness writer runs."
        ),
    )


@st.cache_data(ttl=300, show_spinner=False)
def fetch_insight_summary_placeholder() -> tuple[str | None, pd.DataFrame]:
    """Latest weekly insight row (placeholder). Runbook: ``summary_type``, ``is_llm_generated``, ``summary_text``."""
    sql = """
        SELECT id,
               summary_type,
               is_llm_generated,
               summary_text,
               created_at
        FROM dbo.insight_summary
        ORDER BY created_at DESC
        LIMIT 1
    """
    return _read_cross_pair_sql(
        sql,
        params=None,
        missing_table_hint=(
            "`dbo.insight_summary` is not available yet (Pair D). "
            "Summary source labels will appear after the analytics insight writer is wired."
        ),
    )


def max_computed_at(df: pd.DataFrame) -> datetime | None:
    """Latest ``computed_at`` in the top-skills frame, or ``None``."""
    if df.empty or "computed_at" not in df.columns:
        return None
    series = pd.to_datetime(df["computed_at"], utc=True, errors="coerce")
    if series.isna().all():
        return None
    ts = series.max()
    if pd.isna(ts):
        return None
    out = ts.to_pydatetime()
    if out.tzinfo is None:
        return out.replace(tzinfo=timezone.utc)
    return out
