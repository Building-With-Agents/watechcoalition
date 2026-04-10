"""Refresh weekly skill and tool demand aggregate tables (Analytics steps 2 and 3).

Lives under ``agents.analytics.aggregators`` per CLAUDE.md / ARCHITECTURE_DEEP.

Source rows: ``extracted_intelligence`` JSONB (skills/tools), joined to
``normalized_jobs`` → ``job_postings`` → ``companies`` for spam gating and
distinct ``company_id`` (IMP-021 uses ``company_name`` in examples; we use
``company_id`` for stable deduplication).

Aggregation uses SQLAlchemy ``func.count`` / ``func.distinct`` + ``GROUP BY``
on a DB-side unnest subquery — no Python/Pandas counting.

Idempotent refresh per ``week_start``: DELETE existing rows for that week, then
``INSERT ... SELECT`` via ``insert().from_select``.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import structlog
from sqlalchemy import Date, DateTime, Text, column, delete, func, insert, literal, select, text
from sqlalchemy.orm import Session

from agents.common.data_store.models import SkillDemandWeekly, ToolDemandWeekly
from agents.enrichment.classifiers.spam_preview import get_spam_thresholds

log = structlog.get_logger()

# --- Inner: one row per (posting, skill/tool) in the target week ----------------

_SKILLS_EXPANDED = text(
    """
    SELECT
        (date_trunc('week', COALESCE(jp.publish_date, nj.date_posted)))::date AS week_start,
        NULLIF(
            trim(COALESCE(skel.value->>'skill_name', skel.value->>'label')),
            ''
        ) AS skill_label,
        NULLIF(trim(skel.value->>'esco_uri'), '') AS esco_uri,
        jp.job_posting_id::text AS job_posting_id,
        jp.company_id::text AS company_id
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
        AND (date_trunc('week', COALESCE(jp.publish_date, nj.date_posted)))::date = :week_start
        AND NULLIF(
            trim(COALESCE(skel.value->>'skill_name', skel.value->>'label')),
            ''
        ) IS NOT NULL
    """
).columns(
    column("week_start", Date),
    column("skill_label", Text),
    column("esco_uri", Text),
    column("job_posting_id", Text),
    column("company_id", Text),
)

_TOOLS_EXPANDED = text(
    """
    SELECT
        (date_trunc('week', COALESCE(jp.publish_date, nj.date_posted)))::date AS week_start,
        NULLIF(
            trim(COALESCE(tel.value->>'tool_name', tel.value->>'label')),
            ''
        ) AS tool_label,
        jp.job_posting_id::text AS job_posting_id
    FROM dbo.extracted_intelligence ei
    INNER JOIN dbo.normalized_jobs nj ON nj.id = ei.normalized_job_id
    INNER JOIN dbo.job_postings jp
        ON jp.source IS NOT NULL
        AND jp.external_id IS NOT NULL
        AND nj.source = jp.source
        AND nj.external_id = jp.external_id
    INNER JOIN dbo.companies c ON c.company_id = jp.company_id::text
    CROSS JOIN LATERAL jsonb_array_elements(ei.tools) AS tel(value)
    WHERE NOT ei.extraction_failed
        AND ei.tools IS NOT NULL
        AND jsonb_typeof(ei.tools) = 'array'
        AND jp.is_spam IS NOT TRUE
        AND (jp.spam_score IS NULL OR jp.spam_score <= :reject_threshold)
        AND jp.is_duplicate IS NOT TRUE
        AND (date_trunc('week', COALESCE(jp.publish_date, nj.date_posted)))::date = :week_start
        AND NULLIF(
            trim(COALESCE(tel.value->>'tool_name', tel.value->>'label')),
            ''
        ) IS NOT NULL
    """
).columns(
    column("week_start", Date),
    column("tool_label", Text),
    column("job_posting_id", Text),
)


def refresh_skill_demand_weekly(session: Session, week_start: date) -> int:
    """Delete then recompute ``dbo.skill_demand_weekly`` for ``week_start``.

    Returns number of rows inserted.
    """
    _, reject_threshold = get_spam_thresholds()
    computed_at = datetime.now(timezone.utc)
    binds = {"week_start": week_start, "reject_threshold": reject_threshold}

    expanded = _SKILLS_EXPANDED.subquery("exp_skills")

    agg = (
        select(
            expanded.c.skill_label,
            func.max(expanded.c.esco_uri).label("esco_uri"),
            expanded.c.week_start,
            func.count(func.distinct(expanded.c.job_posting_id)).label("posting_count"),
            func.count(func.distinct(expanded.c.company_id)).label("employer_count"),
            literal(computed_at, type_=DateTime(timezone=True)).label("computed_at"),
        )
        .select_from(expanded)
        .group_by(expanded.c.week_start, expanded.c.skill_label)
    )

    t = SkillDemandWeekly.__table__
    session.execute(delete(t).where(t.c.week_start == week_start))
    result = session.execute(
        insert(t).from_select(
            [
                t.c.skill_label,
                t.c.esco_uri,
                t.c.week_start,
                t.c.posting_count,
                t.c.employer_count,
                t.c.computed_at,
            ],
            agg,
        ),
        binds,
    )
    inserted = result.rowcount or 0
    log.info(
        "skill_demand_weekly_refreshed",
        week_start=str(week_start),
        rows_inserted=inserted,
    )
    return inserted


def refresh_tool_demand_weekly(session: Session, week_start: date) -> int:
    """Delete then recompute ``dbo.tool_demand_weekly`` for ``week_start``.

    Returns number of rows inserted.
    """
    _, reject_threshold = get_spam_thresholds()
    computed_at = datetime.now(timezone.utc)
    binds = {"week_start": week_start, "reject_threshold": reject_threshold}

    expanded = _TOOLS_EXPANDED.subquery("exp_tools")

    agg = (
        select(
            expanded.c.tool_label,
            expanded.c.week_start,
            func.count(func.distinct(expanded.c.job_posting_id)).label("posting_count"),
            literal(computed_at, type_=DateTime(timezone=True)).label("computed_at"),
        )
        .select_from(expanded)
        .group_by(expanded.c.week_start, expanded.c.tool_label)
    )

    t = ToolDemandWeekly.__table__
    session.execute(delete(t).where(t.c.week_start == week_start))
    result = session.execute(
        insert(t).from_select(
            [
                t.c.tool_label,
                t.c.week_start,
                t.c.posting_count,
                t.c.computed_at,
            ],
            agg,
        ),
        binds,
    )
    inserted = result.rowcount or 0
    log.info(
        "tool_demand_weekly_refreshed",
        week_start=str(week_start),
        rows_inserted=inserted,
    )
    return inserted
