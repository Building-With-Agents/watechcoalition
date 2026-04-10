"""Weekly industry-sector rollups (Analytics pipeline Step 6).

``compute_salary_percentiles`` (Pair C) groups by a single column (``naics_code``,
``soc_code``, or ``borderplex_subregion``) with **no** ``week_start`` dimension, so it
cannot drive Step 6 directly. This module uses the same salary expression as
:data:`agents.analytics.aggregators.salary_percentiles.SALARY_VALUE_SQL` and applies
``percentile_disc(0.5)`` in SQL grouped by ``industry_sectors.sector_title`` and week.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import structlog
from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from agents.analytics.aggregators.salary_percentiles import SALARY_VALUE_SQL
from agents.common.data_store.models import SectorSummaryWeekly

log = structlog.get_logger()


def compute_sector_summary_weekly(session: Session, week_start: date) -> list[SectorSummaryWeekly]:
    """
    Aggregate ``dbo.job_postings`` for ``week_start`` (UTC, ``publish_date`` in
    ``[week_start, week_start + 7 days)``) by industry sector title.

    * ``posting_count`` — rows per sector-week
    * ``employer_count`` — distinct ``companies.company_name`` (non-empty)
    * ``avg_salary`` — median (p50) of the shared salary metric (midpoint min/max, else max, else min)
    * ``top_skills`` — top 10 most frequent ``skill_name`` values from ``extracted_intelligence.skills`` JSONB

    Groups with ``COUNT(*) < 5`` are omitted (``HAVING``).
    """
    bind = session.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        log.warning(
            "sector_summary_weekly_unsupported_dialect",
            dialect=getattr(getattr(bind, "dialect", None), "name", None),
        )
        raise NotImplementedError("compute_sector_summary_weekly requires PostgreSQL")

    week_end = week_start + timedelta(days=7)
    ws = datetime.combine(week_start, time.min, tzinfo=timezone.utc)
    we = datetime.combine(week_end, time.min, tzinfo=timezone.utc)
    computed_at = datetime.now(timezone.utc)

    log.info("sector_summary_weekly_compute_start", week_start=str(week_start))

    session.execute(delete(SectorSummaryWeekly).where(SectorSummaryWeekly.week_start == week_start))

    sql = text(
        f"""
        WITH base AS (
            SELECT
                COALESCE(
                    NULLIF(TRIM(BOTH FROM isec.sector_title::text), ''),
                    'Unknown'
                ) AS sector_label,
                jp.job_posting_id,
                nj.id AS nj_id,
                NULLIF(TRIM(BOTH FROM c.company_name::text), '') AS company_name,
                {SALARY_VALUE_SQL} AS salary_value
            FROM dbo.job_postings jp
            INNER JOIN dbo.normalized_jobs nj
                ON nj.source = jp.source
                AND nj.external_id = jp.external_id
            LEFT JOIN dbo.industry_sectors isec
                ON jp.sector_id::text = isec.industry_sector_id
            LEFT JOIN dbo.companies c
                ON jp.company_id::text = c.company_id
            WHERE jp.publish_date IS NOT NULL
              AND jp.publish_date >= :week_start_ts
              AND jp.publish_date < :week_end_ts
              AND jp.source IS NOT NULL
              AND jp.external_id IS NOT NULL
        ),
        agg AS (
            SELECT
                sector_label,
                COUNT(*)::integer AS posting_count,
                COUNT(DISTINCT company_name)::integer AS employer_count,
                percentile_disc(0.5) WITHIN GROUP (ORDER BY salary_value)
                    FILTER (WHERE salary_value IS NOT NULL) AS p50_salary
            FROM base
            GROUP BY sector_label
            HAVING COUNT(*) >= 5
        ),
        skill_counts AS (
            SELECT
                b.sector_label,
                LOWER(TRIM(BOTH FROM je.elem->>'skill_name')) AS skill_name,
                COUNT(*)::bigint AS cnt
            FROM base b
            INNER JOIN dbo.extracted_intelligence ei
                ON ei.normalized_job_id = b.nj_id
            CROSS JOIN LATERAL jsonb_array_elements(COALESCE(ei.skills, '[]'::jsonb))
                AS je(elem)
            WHERE je.elem->>'skill_name' IS NOT NULL
              AND TRIM(BOTH FROM je.elem->>'skill_name') <> ''
            GROUP BY b.sector_label, skill_name
        ),
        skill_top AS (
            SELECT
                sector_label,
                skill_name,
                cnt,
                ROW_NUMBER() OVER (
                    PARTITION BY sector_label
                    ORDER BY cnt DESC, skill_name
                ) AS rn
            FROM skill_counts
        ),
        top_agg AS (
            SELECT
                sector_label,
                COALESCE(
                    jsonb_agg(skill_name ORDER BY cnt DESC, skill_name)
                        FILTER (WHERE rn <= 10),
                    '[]'::jsonb
                ) AS top_skills
            FROM skill_top
            WHERE rn <= 10
            GROUP BY sector_label
        )
        SELECT
            a.sector_label,
            a.posting_count,
            a.employer_count,
            a.p50_salary,
            COALESCE(ta.top_skills, '[]'::jsonb) AS top_skills
        FROM agg a
        LEFT JOIN top_agg ta ON ta.sector_label = a.sector_label
        ORDER BY a.sector_label
        """
    )

    rows = session.execute(
        sql,
        {"week_start_ts": ws, "week_end_ts": we},
    ).mappings().all()

    result: list[SectorSummaryWeekly] = []
    for row in rows:
        raw_skills = row["top_skills"]
        if raw_skills is None:
            skills_list: list[str] = []
        elif isinstance(raw_skills, list):
            skills_list = [str(s) for s in raw_skills]
        else:
            skills_list = list(raw_skills) if hasattr(raw_skills, "__iter__") else []

        result.append(
            SectorSummaryWeekly(
                week_start=week_start,
                sector=str(row["sector_label"]),
                posting_count=int(row["posting_count"]),
                employer_count=int(row["employer_count"]),
                avg_salary=float(row["p50_salary"]) if row["p50_salary"] is not None else None,
                top_skills=skills_list,
                computed_at=computed_at,
            )
        )

    session.add_all(result)

    log.info(
        "sector_summary_weekly_compute_complete",
        week_start=str(week_start),
        sector_row_count=len(result),
        total_postings=sum(r.posting_count for r in result),
    )
    return result
