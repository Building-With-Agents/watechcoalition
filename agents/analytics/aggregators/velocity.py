"""Skill demand velocity (Analytics step 8) from ``skill_demand_weekly``.

Uses **Pandas** for 4-week rolling means and week-over-week ``pct_change`` per
IMP-021 / runbook. ``target_week`` must be the same Monday-anchored ``DATE`` as
``date_trunc('week', ...)::date`` in :mod:`agents.analytics.aggregators.demand_weekly`.

Run **step 2** for ``target_week`` before this refresh so ``demand_count`` and
``esco_uri`` match that week.

Trend classification is **not** driven by raw single-week spikes: demand is
first smoothed with a **4-week rolling mean** along time, then
``pct_change`` compares the latest two smoothed values (WoW on the smoothed
series). ``pct_change`` can yield ``inf`` when the prior rolling mean is zero;
we **classify** using that value (``inf`` → ``accelerating``, ``-inf`` →
``declining``) but persist **``week_over_week_change``** as finite floats
(``0.0`` when non-finite) so the DB never stores NaN/inf.
"""

from __future__ import annotations

import math
from datetime import date, timedelta

import pandas as pd
import structlog
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from agents.common.data_store.models import SkillDemandWeekly, SkillVelocity

log = structlog.get_logger()

ACCELERATING_THRESHOLD = 0.15
DECLINING_THRESHOLD = -0.15
STABLE_THRESHOLD = 0.05
TREND_CONFIDENCE_DEFAULT = 0.8

_NUM_WEEKS_HISTORY = 5
# Rolling mean window (weeks) before WoW pct_change — must stay aligned with runbook / IMP-021.
ROLLING_WINDOW_WEEKS = 4


def _week_starts_for_velocity(target_week: date) -> list[date]:
    """Return ``_NUM_WEEKS_HISTORY`` consecutive week anchors ending at ``target_week`` (oldest first)."""
    return [target_week - timedelta(days=7 * i) for i in range(_NUM_WEEKS_HISTORY - 1, -1, -1)]


def _classify_trend(c: float | int | None) -> str:
    """Map rolling pct-change to IMP-021 trend bucket (raw ``c``, before DB sanitization)."""
    try:
        x = float(c)
    except (TypeError, ValueError):
        return "emerging"
    if math.isnan(x) or pd.isna(c):
        return "emerging"
    if math.isinf(x):
        return "accelerating" if x > 0 else "declining"
    if x > ACCELERATING_THRESHOLD:
        return "accelerating"
    if x < DECLINING_THRESHOLD:
        return "declining"
    if abs(x) <= STABLE_THRESHOLD:
        return "stable"
    return "volatile"


def _sanitize_pct_for_db(c: float | int | None) -> float:
    """Finite float for ``week_over_week_change`` column (never NaN/inf)."""
    try:
        x = float(c)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(x) or math.isinf(x):
        return 0.0
    return x


def _compute_latest_pct_change(pivoted: pd.DataFrame) -> pd.Series:
    """Runbook pipeline: rolling mean then pct_change along time axis."""
    col_order = sorted(pivoted.columns, key=lambda d: d)
    ordered = pivoted[col_order]
    rolling = ordered.T.rolling(window=ROLLING_WINDOW_WEEKS, min_periods=2).mean().T
    latest_pct = rolling.pct_change(axis=1, fill_method=None).iloc[:, -1]
    return latest_pct


def refresh_skill_velocity(session: Session, target_week: date) -> int:
    """Delete ``skill_velocity`` rows for ``target_week``, recompute from demand history, insert.

    Loads the last five ``week_start`` values from ``skill_demand_weekly`` ending at
    ``target_week``, builds trends, and inserts one row per skill seen in that window.

    Returns number of rows inserted.
    """
    week_starts = _week_starts_for_velocity(target_week)
    stmt = select(
        SkillDemandWeekly.skill_label,
        SkillDemandWeekly.week_start,
        SkillDemandWeekly.posting_count,
        SkillDemandWeekly.esco_uri,
    ).where(SkillDemandWeekly.week_start.in_(week_starts))

    demand_df = pd.read_sql(stmt, session.connection())

    tbl = SkillVelocity.__table__
    session.execute(delete(tbl).where(tbl.c.week == target_week))

    if demand_df.empty:
        log.info("skill_velocity_refreshed_empty_history", target_week=str(target_week), rows_inserted=0)
        return 0

    demand_df = demand_df.copy()
    demand_df["week_start"] = pd.to_datetime(demand_df["week_start"]).dt.date

    esco_target = demand_df[demand_df["week_start"] == target_week]
    esco_by_skill: dict[str, str | None] = {}
    for _, r in esco_target.iterrows():
        label = str(r["skill_label"])
        uri = r["esco_uri"]
        esco_by_skill[label] = None if pd.isna(uri) or uri is None else str(uri)

    pivoted = demand_df.pivot_table(
        index="skill_label",
        columns="week_start",
        values="posting_count",
        aggfunc="sum",
    ).fillna(0)

    if target_week not in pivoted.columns:
        missing_cols = [w for w in week_starts if w not in pivoted.columns]
        for w in missing_cols:
            pivoted[w] = 0

    latest_pct = _compute_latest_pct_change(pivoted)

    rows: list[dict] = []
    for skill_label in pivoted.index:
        sl = str(skill_label)
        raw_pct = latest_pct.loc[skill_label] if skill_label in latest_pct.index else float("nan")
        trend = _classify_trend(raw_pct)
        woc = _sanitize_pct_for_db(raw_pct)

        demand_count = int(pivoted.loc[skill_label, target_week]) if target_week in pivoted.columns else 0

        rows.append(
            {
                "skill_label": sl,
                "esco_uri": esco_by_skill.get(sl),
                "week": target_week,
                "demand_count": demand_count,
                "week_over_week_change": woc,
                "four_week_trend": trend,
                "trend_confidence": TREND_CONFIDENCE_DEFAULT,
            }
        )

    if not rows:
        log.info("skill_velocity_refreshed_no_rows", target_week=str(target_week), rows_inserted=0)
        return 0

    session.execute(insert(tbl), rows)
    inserted = len(rows)
    log.info("skill_velocity_refreshed", target_week=str(target_week), rows_inserted=inserted)
    return inserted
