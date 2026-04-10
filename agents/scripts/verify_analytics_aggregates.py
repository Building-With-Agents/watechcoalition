#!/usr/bin/env python3
"""Cross-check Week 7 Pair A aggregates vs manual SQL (issues #176 / #177).

Runs verification for a target **Monday** ``week_start`` (same anchor as
``date_trunc('week', ...)`` in ``demand_weekly``):

- **Step 2** — ``skill_demand_weekly``: sum of ``posting_count`` vs reconciled sum
  from expanded skills (same as ``verify_aggregates.py``).
- **Step 3** — ``tool_demand_weekly``: same pattern for tools.
- **Step 8** — ``skill_velocity``: ``demand_count`` / ``esco_uri`` vs
  ``skill_demand_weekly`` for that week; orphan detection.
- **Step 9** — ``skill_co_occurrence``: lexicographic order, row cap ≤ 200,
  top-200 pair counts vs manual SQL (matches ``co_occurrence.py``).

**Prerequisite:** Refresh aggregates for ``--week`` before running (steps 2–3
before 8–9).

**Usage** (repo root)::

    PYTHONPATH=. python agents/scripts/verify_analytics_aggregates.py --week 2026-03-30

    PYTHONPATH=. python agents/scripts/verify_analytics_aggregates.py --week 2026-03-30 --only skills,tools

    PYTHONPATH=. python agents/scripts/verify_analytics_aggregates.py --week 2026-03-30 --drift-threshold-pct 0.5

Requires ``PYTHON_DATABASE_URL`` and spam thresholds via ``get_spam_thresholds()``.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_REPO_ROOT / ".env")

import structlog  # noqa: E402

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(colors=False),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
from sqlalchemy import func, select, text  # noqa: E402

from agents.analytics.aggregators.demand_weekly import (  # noqa: E402
    _SKILLS_EXPANDED,
    _TOOLS_EXPANDED,
)
from agents.common.data_store.database import session_scope  # noqa: E402
from agents.common.data_store.models import SkillDemandWeekly, ToolDemandWeekly  # noqa: E402
from agents.enrichment.classifiers.spam_preview import get_spam_thresholds  # noqa: E402

log = structlog.get_logger()

_TOP_PAIR_LIMIT = 200


def parse_target_week(s: str) -> date:
    raw = s.strip()
    collapsed = raw.replace(" ", "").upper()
    if collapsed in ("YYYY-MM-DD", "<YYYY-MM-DD>"):
        raise ValueError("Use a real Monday date, e.g. --week 2026-03-30")
    return date.fromisoformat(raw[:10])


def default_target_week(reference: datetime | None = None) -> date:
    ref = reference if reference is not None else datetime.now(timezone.utc)
    d = ref.date()
    this_monday = d - timedelta(days=d.weekday())
    return this_monday - timedelta(days=7)


def _drift_percent(aggregate: int, truth: int) -> float:
    if aggregate == 0 and truth == 0:
        return 0.0
    denom = max(abs(aggregate), abs(truth), 1)
    return abs(aggregate - truth) / denom * 100.0


def _skill_truth_sum(session, target_week: date, reject_threshold: float) -> int:
    expanded = _SKILLS_EXPANDED.subquery("exp_skills")
    per_skill = (
        select(
            expanded.c.skill_label,
            func.count(func.distinct(expanded.c.job_posting_id)).label("per_skill_cnt"),
        )
        .select_from(expanded)
        .group_by(expanded.c.skill_label)
    ).subquery("per_skill")
    stmt = select(func.coalesce(func.sum(per_skill.c.per_skill_cnt), 0))
    row = session.execute(stmt, {"week_start": target_week, "reject_threshold": reject_threshold}).scalar()
    return int(row or 0)


def _skill_aggregate_sum(session, target_week: date) -> int:
    stmt = select(func.coalesce(func.sum(SkillDemandWeekly.posting_count), 0)).where(
        SkillDemandWeekly.week_start == target_week
    )
    return int(session.execute(stmt).scalar() or 0)


def _tool_truth_sum(session, target_week: date, reject_threshold: float) -> int:
    expanded = _TOOLS_EXPANDED.subquery("exp_tools")
    per_tool = (
        select(
            expanded.c.tool_label,
            func.count(func.distinct(expanded.c.job_posting_id)).label("per_tool_cnt"),
        )
        .select_from(expanded)
        .group_by(expanded.c.tool_label)
    ).subquery("per_tool")
    stmt = select(func.coalesce(func.sum(per_tool.c.per_tool_cnt), 0))
    row = session.execute(stmt, {"week_start": target_week, "reject_threshold": reject_threshold}).scalar()
    return int(row or 0)


def _tool_aggregate_sum(session, target_week: date) -> int:
    stmt = select(func.coalesce(func.sum(ToolDemandWeekly.posting_count), 0)).where(
        ToolDemandWeekly.week_start == target_week
    )
    return int(session.execute(stmt).scalar() or 0)


def _skill_per_row_mismatch_count(session, target_week: date, reject_threshold: float) -> int:
    """Count skill_label rows where manual distinct postings != aggregate posting_count."""
    sql = text(
        """
        WITH exp AS (
            SELECT
                NULLIF(trim(COALESCE(skel.value->>'skill_name', skel.value->>'label')), '') AS skill_label,
                jp.job_posting_id::text AS job_posting_id
            FROM dbo.extracted_intelligence ei
            INNER JOIN dbo.normalized_jobs nj ON nj.id = ei.normalized_job_id
            INNER JOIN dbo.job_postings jp
                ON jp.source IS NOT NULL AND jp.external_id IS NOT NULL
                AND nj.source = jp.source AND nj.external_id = jp.external_id
            INNER JOIN dbo.companies c ON c.company_id = jp.company_id::text
            CROSS JOIN LATERAL jsonb_array_elements(ei.skills) AS skel(value)
            WHERE NOT ei.extraction_failed
              AND ei.skills IS NOT NULL AND jsonb_typeof(ei.skills) = 'array'
              AND jp.is_spam IS NOT TRUE
              AND (jp.spam_score IS NULL OR jp.spam_score <= :reject_threshold)
              AND jp.is_duplicate IS NOT TRUE
              AND (date_trunc('week', COALESCE(jp.publish_date, nj.date_posted)))::date = :week_start
              AND NULLIF(trim(COALESCE(skel.value->>'skill_name', skel.value->>'label')), '') IS NOT NULL
        ),
        manual AS (
            SELECT skill_label, COUNT(DISTINCT job_posting_id)::bigint AS posting_cnt
            FROM exp GROUP BY skill_label
        )
        SELECT COUNT(*)::bigint
        FROM manual m
        FULL OUTER JOIN dbo.skill_demand_weekly a
          ON a.skill_label = m.skill_label AND a.week_start = :week_start
        WHERE COALESCE(m.posting_cnt, 0) IS DISTINCT FROM COALESCE(a.posting_count, 0)
        """
    )
    row = session.execute(sql, {"week_start": target_week, "reject_threshold": reject_threshold}).scalar()
    return int(row or 0)


def _tool_per_row_mismatch_count(session, target_week: date, reject_threshold: float) -> int:
    sql = text(
        """
        WITH exp AS (
            SELECT
                NULLIF(trim(COALESCE(tel.value->>'tool_name', tel.value->>'label')), '') AS tool_label,
                jp.job_posting_id::text AS job_posting_id
            FROM dbo.extracted_intelligence ei
            INNER JOIN dbo.normalized_jobs nj ON nj.id = ei.normalized_job_id
            INNER JOIN dbo.job_postings jp
                ON jp.source IS NOT NULL AND jp.external_id IS NOT NULL
                AND nj.source = jp.source AND nj.external_id = jp.external_id
            INNER JOIN dbo.companies c ON c.company_id = jp.company_id::text
            CROSS JOIN LATERAL jsonb_array_elements(ei.tools) AS tel(value)
            WHERE NOT ei.extraction_failed
              AND ei.tools IS NOT NULL AND jsonb_typeof(ei.tools) = 'array'
              AND jp.is_spam IS NOT TRUE
              AND (jp.spam_score IS NULL OR jp.spam_score <= :reject_threshold)
              AND jp.is_duplicate IS NOT TRUE
              AND (date_trunc('week', COALESCE(jp.publish_date, nj.date_posted)))::date = :week_start
              AND NULLIF(trim(COALESCE(tel.value->>'tool_name', tel.value->>'label')), '') IS NOT NULL
        ),
        manual AS (
            SELECT tool_label, COUNT(DISTINCT job_posting_id)::bigint AS posting_cnt
            FROM exp GROUP BY tool_label
        )
        SELECT COUNT(*)::bigint
        FROM manual m
        FULL OUTER JOIN dbo.tool_demand_weekly a
          ON a.tool_label = m.tool_label AND a.week_start = :week_start
        WHERE COALESCE(m.posting_cnt, 0) IS DISTINCT FROM COALESCE(a.posting_count, 0)
        """
    )
    row = session.execute(sql, {"week_start": target_week, "reject_threshold": reject_threshold}).scalar()
    return int(row or 0)


def _velocity_demand_mismatch_count(session, target_week: date) -> int:
    sql = text(
        """
        SELECT COUNT(*)::bigint
        FROM dbo.skill_velocity v
        INNER JOIN dbo.skill_demand_weekly d
          ON d.skill_label = v.skill_label AND d.week_start = v.week
        WHERE v.week = :week_start
          AND v.demand_count IS DISTINCT FROM d.posting_count
        """
    )
    return int(session.execute(sql, {"week_start": target_week}).scalar() or 0)


def _velocity_esco_mismatch_count(session, target_week: date) -> int:
    sql = text(
        """
        SELECT COUNT(*)::bigint
        FROM dbo.skill_velocity v
        INNER JOIN dbo.skill_demand_weekly d
          ON d.skill_label = v.skill_label AND d.week_start = v.week
        WHERE v.week = :week_start
          AND v.esco_uri IS DISTINCT FROM d.esco_uri
        """
    )
    return int(session.execute(sql, {"week_start": target_week}).scalar() or 0)


def _velocity_orphan_count(session, target_week: date) -> int:
    sql = text(
        """
        SELECT COUNT(*)::bigint
        FROM dbo.skill_velocity v
        LEFT JOIN dbo.skill_demand_weekly d
          ON d.skill_label = v.skill_label AND d.week_start = v.week
        WHERE v.week = :week_start AND d.skill_label IS NULL
        """
    )
    return int(session.execute(sql, {"week_start": target_week}).scalar() or 0)


def _cooccurrence_bad_lex_count(session, target_week: date) -> int:
    """Flag ``skill_a = skill_b`` or ``skill_a > skill_b`` under C collation (Python-like code-point order)."""
    sql = text(
        """
        SELECT COUNT(*)::bigint
        FROM dbo.skill_co_occurrence
        WHERE week_start = :week_start
          AND (
            skill_a = skill_b
            OR (skill_a COLLATE "C") > (skill_b COLLATE "C")
          )
        """
    )
    return int(session.execute(sql, {"week_start": target_week}).scalar() or 0)


def _cooccurrence_row_count(session, target_week: date) -> int:
    sql = text(
        """
        SELECT COUNT(*)::bigint FROM dbo.skill_co_occurrence WHERE week_start = :week_start
        """
    )
    return int(session.execute(sql, {"week_start": target_week}).scalar() or 0)


def _cooccurrence_top200_mismatch_count(session, target_week: date, reject_threshold: float) -> int:
    """Pairs where manual top-200 count != stored row (full outer join)."""
    sql = text(
        """
        WITH exp AS (
            SELECT jp.job_posting_id::text AS job_posting_id,
                   NULLIF(trim(COALESCE(skel.value->>'skill_name', skel.value->>'label')), '') AS skill_label
            FROM dbo.extracted_intelligence ei
            INNER JOIN dbo.normalized_jobs nj ON nj.id = ei.normalized_job_id
            INNER JOIN dbo.job_postings jp
                ON jp.source IS NOT NULL AND jp.external_id IS NOT NULL
                AND nj.source = jp.source AND nj.external_id = jp.external_id
            INNER JOIN dbo.companies c ON c.company_id = jp.company_id::text
            CROSS JOIN LATERAL jsonb_array_elements(ei.skills) AS skel(value)
            WHERE NOT ei.extraction_failed
              AND ei.skills IS NOT NULL AND jsonb_typeof(ei.skills) = 'array'
              AND jp.is_spam IS NOT TRUE
              AND (jp.spam_score IS NULL OR jp.spam_score <= :reject_threshold)
              AND jp.is_duplicate IS NOT TRUE
              AND (date_trunc('week', COALESCE(jp.publish_date, nj.date_posted)))::date = :week_start
              AND NULLIF(trim(COALESCE(skel.value->>'skill_name', skel.value->>'label')), '') IS NOT NULL
        ),
        dedup AS (
            SELECT DISTINCT job_posting_id, skill_label FROM exp
        ),
        ranked AS (
            SELECT job_posting_id, skill_label,
                   ROW_NUMBER() OVER (
                       PARTITION BY job_posting_id
                       ORDER BY skill_label COLLATE "C"
                   ) AS rn
            FROM dedup
        ),
        capped AS (
            SELECT job_posting_id, skill_label FROM ranked WHERE rn <= 20
        ),
        pairs AS (
            SELECT x.job_posting_id,
                   CASE
                       WHEN (x.skill_label COLLATE "C") < (y.skill_label COLLATE "C")
                       THEN x.skill_label
                       ELSE y.skill_label
                   END AS skill_a,
                   CASE
                       WHEN (x.skill_label COLLATE "C") < (y.skill_label COLLATE "C")
                       THEN y.skill_label
                       ELSE x.skill_label
                   END AS skill_b
            FROM capped x
            INNER JOIN capped y
              ON x.job_posting_id = y.job_posting_id
             AND (x.skill_label COLLATE "C") < (y.skill_label COLLATE "C")
        ),
        manual AS (
            SELECT skill_a, skill_b, COUNT(*)::bigint AS manual_cnt
            FROM pairs
            GROUP BY skill_a, skill_b
        ),
        top200 AS (
            SELECT skill_a, skill_b, manual_cnt
            FROM manual
            ORDER BY manual_cnt DESC, skill_a COLLATE "C", skill_b COLLATE "C"
            LIMIT :top_limit
        )
        SELECT COUNT(*)::bigint
        FROM top200 t
        FULL OUTER JOIN dbo.skill_co_occurrence s
          ON s.skill_a = t.skill_a AND s.skill_b = t.skill_b AND s.week_start = :week_start
        WHERE COALESCE(t.manual_cnt, 0) IS DISTINCT FROM COALESCE(s.co_occurrence_count, 0)
        """
    )
    row = session.execute(
        sql,
        {
            "week_start": target_week,
            "reject_threshold": reject_threshold,
            "top_limit": _TOP_PAIR_LIMIT,
        },
    ).scalar()
    return int(row or 0)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify skill/tool demand, velocity, and co-occurrence aggregates vs manual SQL."
    )
    parser.add_argument(
        "--week",
        type=str,
        default=None,
        help="Monday week_start (YYYY-MM-DD). Default: prior ISO week Monday (UTC).",
    )
    parser.add_argument(
        "--drift-threshold-pct",
        type=float,
        default=0.5,
        help="Max allowed drift %% for steps 2 and 3 global sums (default 0.5 = IMP-021).",
    )
    parser.add_argument(
        "--only",
        type=str,
        default="all",
        help="Comma-separated: skills,tools,velocity,cooccurrence,all (default all).",
    )
    args = parser.parse_args()

    if not os.getenv("PYTHON_DATABASE_URL"):
        log.error("verify_analytics_aggregates_fail", reason="PYTHON_DATABASE_URL not set")
        return 1

    try:
        target_week = parse_target_week(args.week) if args.week else default_target_week()
    except ValueError as exc:
        log.error("verify_analytics_aggregates_fail", reason=str(exc))
        return 1

    only = {x.strip().lower() for x in args.only.split(",")}
    if "all" in only:
        run_skills = run_tools = run_velocity = run_cooccurrence = True
    else:
        run_skills = "skills" in only
        run_tools = "tools" in only
        run_velocity = "velocity" in only
        run_cooccurrence = "cooccurrence" in only

    _, reject_threshold = get_spam_thresholds()
    drift_max = args.drift_threshold_pct
    failed = False

    with session_scope() as session:
        log.info(
            "verify_analytics_aggregates_start",
            week_start=str(target_week),
            reject_threshold=reject_threshold,
            drift_threshold_pct=drift_max,
        )

        if run_skills:
            truth_s = _skill_truth_sum(session, target_week, reject_threshold)
            agg_s = _skill_aggregate_sum(session, target_week)
            drift_s = _drift_percent(agg_s, truth_s)
            mism_s = _skill_per_row_mismatch_count(session, target_week, reject_threshold)
            ok_s = drift_s <= drift_max and mism_s == 0
            log.info(
                "verify_step2_skill_demand_weekly",
                manual_reconciled_sum=truth_s,
                aggregate_sum_posting_count=agg_s,
                drift_pct=round(drift_s, 6),
                per_skill_mismatch_rows=mism_s,
                pass_=ok_s,
            )
            if not ok_s:
                failed = True

        if run_tools:
            truth_t = _tool_truth_sum(session, target_week, reject_threshold)
            agg_t = _tool_aggregate_sum(session, target_week)
            drift_t = _drift_percent(agg_t, truth_t)
            mism_t = _tool_per_row_mismatch_count(session, target_week, reject_threshold)
            ok_t = drift_t <= drift_max and mism_t == 0
            log.info(
                "verify_step3_tool_demand_weekly",
                manual_reconciled_sum=truth_t,
                aggregate_sum_posting_count=agg_t,
                drift_pct=round(drift_t, 6),
                per_tool_mismatch_rows=mism_t,
                pass_=ok_t,
            )
            if not ok_t:
                failed = True

        if run_velocity:
            n_vel = int(
                session.execute(
                    text("SELECT COUNT(*)::bigint FROM dbo.skill_velocity WHERE week = :w"),
                    {"w": target_week},
                ).scalar()
                or 0
            )
            dm = _velocity_demand_mismatch_count(session, target_week)
            em = _velocity_esco_mismatch_count(session, target_week)
            orph = _velocity_orphan_count(session, target_week)
            ok_v = dm == 0 and em == 0 and orph == 0
            if n_vel == 0:
                log.info(
                    "verify_step8_skill_velocity",
                    rows_for_week=0,
                    message="No skill_velocity rows for this week — run refresh_skill_velocity after step 2.",
                    pass_=True,
                )
            else:
                log.info(
                    "verify_step8_skill_velocity",
                    rows_for_week=n_vel,
                    demand_count_mismatches=dm,
                    esco_uri_mismatches=em,
                    orphan_rows=orph,
                    pass_=ok_v,
                )
                if not ok_v:
                    failed = True

        if run_cooccurrence:
            n_co = _cooccurrence_row_count(session, target_week)
            bad_lex = _cooccurrence_bad_lex_count(session, target_week)
            top_mismatch = _cooccurrence_top200_mismatch_count(session, target_week, reject_threshold)
            ok_lex = bad_lex == 0
            ok_cap = n_co <= _TOP_PAIR_LIMIT
            ok_top = top_mismatch == 0
            ok_c = ok_lex and ok_cap and ok_top
            if n_co == 0:
                log.info(
                    "verify_step9_skill_co_occurrence",
                    rows_for_week=0,
                    message="No skill_co_occurrence rows — run refresh_skill_co_occurrence after step 2.",
                    pass_=True,
                )
            else:
                log.info(
                    "verify_step9_skill_co_occurrence",
                    rows_for_week=n_co,
                    bad_lexicographic_pairs=bad_lex,
                    top200_pair_mismatches=top_mismatch,
                    pass_=ok_c,
                )
                if not ok_c:
                    failed = True

    if failed:
        log.error(
            "verify_analytics_aggregates_fail",
            week_start=str(target_week),
            hint="Refresh aggregates for this week or fix implementation; see log lines above.",
        )
        return 1

    log.info("verify_analytics_aggregates_pass", week_start=str(target_week))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
