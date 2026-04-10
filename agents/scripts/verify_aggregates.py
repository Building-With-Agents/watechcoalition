#!/usr/bin/env python3
"""IMP-021 / Week 7 — verify ``skill_demand_weekly`` against Step 2 ground truth.

Compares the **sum of ``posting_count``** over all skills for a target ISO week to
the same quantity recomputed from raw enriched data using the same logic as
``agents.analytics.aggregators.demand_weekly._SKILLS_EXPANDED`` (per-skill
``COUNT(DISTINCT job_posting_id)``, then summed). Those two totals must match
within **0.5%** (IMP-021 aggregate accuracy).

**Note:** A single global ``COUNT(DISTINCT job_posting_id)`` over the expanded
rows counts *postings*, not *skill–posting pairs*. It is **not** comparable to
``SUM(posting_count)`` when postings have multiple skills. This script prints
that distinct-posting count separately for coverage visibility only; the exit
code uses the **reconciled** sum comparison only.

**Run locally** (repo root)::

    PYTHONPATH=. python agents/scripts/verify_aggregates.py

Optional week: pass a **real** Monday as ISO ``YYYY-MM-DD`` (do **not** type the
placeholder letters ``YYYY-MM-DD``)::

    PYTHONPATH=. python agents/scripts/verify_aggregates.py --week 2025-01-06

List Mondays that have Step-2-eligible expanded skill rows (same joins/filters as
``_SKILLS_EXPANDED``, **no** week filter) — use this to pick ``--week``::

    PYTHONPATH=. python agents/scripts/verify_aggregates.py --list-weeks
    PYTHONPATH=. python agents/scripts/verify_aggregates.py --list-weeks --list-limit 50

Requires ``PYTHON_DATABASE_URL`` and (for spam bound) the same env as production
(``SPAM_REJECT_THRESHOLD`` defaults via ``get_spam_thresholds()``).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Path bootstrap (repo root on sys.path)
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

from agents.analytics.aggregators.demand_weekly import _SKILLS_EXPANDED  # noqa: E402
from agents.common.data_store.database import session_scope  # noqa: E402
from agents.common.data_store.models import SkillDemandWeekly  # noqa: E402
from agents.enrichment.classifiers.spam_preview import get_spam_thresholds  # noqa: E402

log = structlog.get_logger()

# Step 2 shape without ``week_start = :week_start`` — for discovering valid Mondays.
_LIST_WEEKS_SQL = text(
    """
    SELECT
        (date_trunc('week', COALESCE(jp.publish_date, nj.date_posted)))::date AS week_start,
        COUNT(*)::bigint AS expanded_skill_rows,
        COUNT(DISTINCT jp.job_posting_id)::bigint AS distinct_postings
    FROM dbo.extracted_intelligence ei
    INNER JOIN dbo.normalized_jobs nj ON nj.id = ei.normalized_job_id
    INNER JOIN dbo.job_postings jp
        ON jp.source IS NOT NULL
        AND jp.external_id IS NOT NULL
        AND nj.source = jp.source
        AND nj.external_id = jp.external_id
    INNER JOIN dbo.companies c ON c.company_id = jp.company_id::text
    CROSS JOIN LATERAL jsonb_array_elements(ei.skills) AS skel(value)
    WHERE NOT ei.extraction_failed
        AND ei.skills IS NOT NULL
        AND jsonb_typeof(ei.skills) = 'array'
        AND jp.is_spam IS NOT TRUE
        AND (jp.spam_score IS NULL OR jp.spam_score <= :reject_threshold)
        AND jp.is_duplicate IS NOT TRUE
        AND NULLIF(
            trim(COALESCE(skel.value->>'skill_name', skel.value->>'label')),
            ''
        ) IS NOT NULL
    GROUP BY 1
    ORDER BY 1 DESC
    LIMIT :list_limit
    """
)


def default_target_week(reference: datetime | None = None) -> date:
    """Prior ISO week Monday (UTC), same default as analytics aggregate refresh."""
    ref = reference if reference is not None else datetime.now(timezone.utc)
    d = ref.date()
    this_monday = d - timedelta(days=d.weekday())
    return this_monday - timedelta(days=7)


def parse_target_week(s: str) -> date:
    """Parse ``--week`` as ISO date; reject doc placeholders and bad strings."""
    raw = s.strip()
    collapsed = raw.replace(" ", "").upper()
    if collapsed in ("YYYY-MM-DD", "<YYYY-MM-DD>"):
        raise ValueError("'YYYY-MM-DD' is a documentation placeholder. Use a real Monday, e.g. --week 2025-01-06")
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        raise ValueError(
            f"Invalid --week {raw!r}. Expected ISO date YYYY-MM-DD (Monday week_start), e.g. 2025-01-06"
        ) from None


def _aggregate_sum_posting_counts(session, target_week: date) -> int:
    stmt = select(func.coalesce(func.sum(SkillDemandWeekly.posting_count), 0)).where(
        SkillDemandWeekly.week_start == target_week
    )
    row = session.execute(stmt).scalar()
    return int(row or 0)


def _reconciled_truth_sum(session, target_week: date, reject_threshold: float) -> int:
    """Sum over skills of COUNT(DISTINCT job_posting_id) — matches Step 2 rollup."""
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
    binds = {"week_start": target_week, "reject_threshold": reject_threshold}
    row = session.execute(stmt, binds).scalar()
    return int(row or 0)


def _distinct_postings_informational(session, target_week: date, reject_threshold: float) -> int:
    """Global distinct postings with ≥1 expanded skill row (not equal to sum of posting_count)."""
    expanded = _SKILLS_EXPANDED.subquery("exp_skills")
    stmt = select(func.count(func.distinct(expanded.c.job_posting_id))).select_from(expanded)
    binds = {"week_start": target_week, "reject_threshold": reject_threshold}
    row = session.execute(stmt, binds).scalar()
    return int(row or 0)


def _drift_percent(aggregate: int, truth: int) -> float:
    if aggregate == 0 and truth == 0:
        return 0.0
    denom = max(abs(aggregate), abs(truth), 1)
    return abs(aggregate - truth) / denom * 100.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify skill_demand_weekly vs Step 2 SQL (IMP-021)")
    parser.add_argument(
        "--list-weeks",
        action="store_true",
        help="Print Mondays (week_start) that have Step-2-style expanded skill rows; then exit 0.",
    )
    parser.add_argument(
        "--list-limit",
        type=int,
        default=30,
        metavar="N",
        help="With --list-weeks, max number of week rows to print (default: 30).",
    )
    parser.add_argument(
        "--week",
        type=str,
        default=None,
        metavar="DATE",
        help="Monday week_start as ISO date, e.g. 2025-01-06 (not the literal YYYY-MM-DD). "
        "Default: prior ISO week Monday (UTC).",
    )
    args = parser.parse_args()

    if not os.getenv("PYTHON_DATABASE_URL"):
        log.error("verify_aggregates_fail", reason="PYTHON_DATABASE_URL not set")
        return 1

    _, reject_threshold = get_spam_thresholds()

    if args.list_weeks:
        with session_scope() as session:
            rows = session.execute(
                _LIST_WEEKS_SQL,
                {"reject_threshold": reject_threshold, "list_limit": args.list_limit},
            ).all()
        if not rows:
            log.info(
                "verify_aggregates_list_weeks_empty",
                message="No expanded skill rows matched Step 2 filters (check data and spam thresholds).",
            )
            return 0
        log.info(
            "verify_aggregates_list_weeks_header",
            message="Use week_start (Monday) with --week. Columns: expanded_skill_rows, distinct_postings.",
        )
        for wk, exp_rows, dist_post in rows:
            log.info(
                "verify_aggregates_list_weeks_row",
                week_start=str(wk),
                expanded_skill_rows=int(exp_rows),
                distinct_postings=int(dist_post),
            )
        return 0

    try:
        target_week = parse_target_week(args.week) if args.week else default_target_week()
    except ValueError as exc:
        log.error("verify_aggregates_fail", reason=str(exc))
        return 1

    with session_scope() as session:
        agg_sum = _aggregate_sum_posting_counts(session, target_week)
        truth_sum = _reconciled_truth_sum(session, target_week, reject_threshold)
        distinct_postings = _distinct_postings_informational(session, target_week, reject_threshold)

    drift = _drift_percent(agg_sum, truth_sum)

    log.info(
        "verify_aggregates_compare",
        target_week=str(target_week),
        aggregate_sum_posting_count=agg_sum,
        manual_reconciled_sum=truth_sum,
        distinct_postings_any_skill=distinct_postings,
        drift_pct=round(drift, 6),
    )

    if drift > 0.5:
        log.error(
            "verify_aggregates_fail",
            drift_pct=round(drift, 6),
            threshold_pct=0.5,
            hint="Re-run refresh_skill_demand_weekly for this week or investigate data skew.",
        )
        return 1

    log.info("verify_aggregates_pass", message="skill_demand_weekly matches Step 2 within 0.5%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
