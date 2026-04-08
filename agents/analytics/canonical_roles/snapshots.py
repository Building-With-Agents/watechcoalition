"""Weekly role snapshots with salary percentiles (Pair C step 5)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from agents.common.data_store.models import RoleSnapshotWeekly
from agents.common.message_bus.comparison import percentile

log = structlog.get_logger()

# TODO issue #188 — swap to Pair B ``compute_salary_percentiles(session, group_col, ...)`` when available.

_WEEK_ROWS_SQL = text(
    """
    SELECT
        jp.canonical_role_id::text AS canonical_role_id,
        cr.label AS role_label,
        cr.top_skills AS top_skills,
        cr.top_tools AS top_tools,
        nj.salary_min AS salary_min,
        nj.salary_max AS salary_max,
        nj.salary_period AS salary_period
    FROM dbo.job_postings jp
    INNER JOIN dbo.normalized_jobs nj
        ON jp.source IS NOT NULL
        AND jp.external_id IS NOT NULL
        AND nj.source = jp.source
        AND nj.external_id = jp.external_id
    LEFT JOIN dbo.canonical_roles cr ON cr.role_id = jp.canonical_role_id
    WHERE jp.canonical_role_id IS NOT NULL
        AND jp.publish_date IS NOT NULL
        AND DATE_TRUNC('week', jp.publish_date AT TIME ZONE 'UTC')::date = :week_start
    """
)


def _annualized_numeric_salary(
    salary_min: float | None,
    salary_max: float | None,
    salary_period: str | None,
) -> float | None:
    """Single scalar salary for percentile math; annualize hourly with 2080 h/yr factor."""
    if salary_min is None and salary_max is None:
        return None
    if salary_min is not None and salary_max is not None:
        mid = (float(salary_min) + float(salary_max)) / 2.0
    elif salary_min is not None:
        mid = float(salary_min)
    else:
        mid = float(salary_max or 0.0)
    if mid <= 0:
        return None
    period = (salary_period or "").strip().lower()
    if period == "hourly":
        return mid * 2080.0
    return mid


def refresh_role_snapshot_weekly(session: Session, *, week_start: date) -> int:
    """Replace all ``role_snapshot_weekly`` rows for ``week_start``.

    Aggregates postings whose ``publish_date`` falls in that ISO week (UTC).
    Populates ``salary_p25``–``salary_p95`` via :func:`percentile` (interim).
    Copies ``top_skills`` / ``top_tools`` from ``canonical_roles`` when present.
    """
    session.execute(
        text("DELETE FROM dbo.role_snapshot_weekly WHERE week_start = :ws"),
        {"ws": week_start},
    )

    rows = session.execute(_WEEK_ROWS_SQL, {"week_start": week_start}).mappings().all()
    by_role: dict[str, dict[str, Any]] = {}
    salaries_by_role: dict[str, list[float]] = defaultdict(list)
    posting_counts: dict[str, int] = defaultdict(int)

    for r in rows:
        rid = r["canonical_role_id"]
        if not rid:
            continue
        posting_counts[rid] += 1
        if rid not in by_role:
            by_role[rid] = {
                "role_title": r["role_label"],
                "top_skills": r["top_skills"],
                "top_tools": r["top_tools"],
            }
        val = _annualized_numeric_salary(
            r["salary_min"],
            r["salary_max"],
            r["salary_period"],
        )
        if val is not None:
            salaries_by_role[rid].append(val)

    now = datetime.now(timezone.utc)
    inserted = 0
    for rid, meta in by_role.items():
        sal = salaries_by_role.get(rid, [])
        p25 = percentile(sal, 25) if sal else None
        p50 = percentile(sal, 50) if sal else None
        p75 = percentile(sal, 75) if sal else None
        p95 = percentile(sal, 95) if sal else None
        avg_s = sum(sal) / len(sal) if sal else None
        median_s = p50

        posting_count = posting_counts[rid]

        row = RoleSnapshotWeekly(
            week_start=week_start,
            canonical_role_id=rid,
            posting_count=posting_count,
            role_title=meta.get("role_title"),
            avg_salary=avg_s,
            median_salary=median_s,
            salary_p25=p25,
            salary_p50=p50,
            salary_p75=p75,
            salary_p95=p95,
            top_skills=meta.get("top_skills"),
            top_tools=meta.get("top_tools"),
            computed_at=now,
        )
        session.add(row)
        inserted += 1

    log.info("role_snapshot_weekly_refreshed", week_start=str(week_start), row_count=inserted)
    return inserted
