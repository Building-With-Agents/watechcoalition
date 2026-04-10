"""Weekly geographic demand aggregates by ``borderplex_subregion`` (Pair B Week 7)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from agents.common.data_store.models import GeoDemandWeekly

log = structlog.get_logger()


def compute_geo_demand_weekly(session: Session, week_start: date) -> list[GeoDemandWeekly]:
    """
    Count ``dbo.job_postings`` rows per ``borderplex_subregion`` for the week beginning
    ``week_start`` (inclusive) through ``week_start + 7 days`` (exclusive), in UTC.

    Returns ORM instances without primary keys set, ready for ``session.add_all`` / bulk insert.
    Rows with NULL ``borderplex_subregion`` are excluded.
    """
    bind = session.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        log.warning(
            "geo_demand_weekly_unsupported_dialect",
            dialect=getattr(getattr(bind, "dialect", None), "name", None),
        )
        raise NotImplementedError("compute_geo_demand_weekly requires PostgreSQL")

    week_end = week_start + timedelta(days=7)
    ws = datetime.combine(week_start, time.min, tzinfo=timezone.utc)
    we = datetime.combine(week_end, time.min, tzinfo=timezone.utc)

    log.info(
        "geo_demand_weekly_compute_start",
        week_start=str(week_start),
        week_end_exclusive=str(week_end),
    )

    sql = text(
        """
        SELECT
            TRIM(BOTH FROM jp.borderplex_subregion::text) AS region,
            COUNT(*)::bigint AS cnt
        FROM dbo.job_postings jp
        WHERE jp.publish_date IS NOT NULL
          AND jp.publish_date >= :week_start_ts
          AND jp.publish_date < :week_end_ts
          AND jp.borderplex_subregion IS NOT NULL
          AND TRIM(BOTH FROM jp.borderplex_subregion::text) <> ''
        GROUP BY TRIM(BOTH FROM jp.borderplex_subregion::text)
        ORDER BY region
        """
    )

    rows = session.execute(
        sql,
        {"week_start_ts": ws, "week_end_ts": we},
    ).mappings().all()

    result: list[GeoDemandWeekly] = []
    for row in rows:
        result.append(
            GeoDemandWeekly(
                week_start=week_start,
                borderplex_subregion=str(row["region"])[:32],
                posting_count=int(row["cnt"]),
            )
        )

    log.info(
        "geo_demand_weekly_compute_complete",
        week_start=str(week_start),
        region_count=len(result),
        total_postings=sum(r.posting_count for r in result),
    )
    return result
