"""Shared salary percentile aggregates for analytics tables."""

from __future__ import annotations

from datetime import date

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

log = structlog.get_logger()

# SQL fragments on ``dbo.job_postings`` alias ``jp`` — never pass unvalidated user input as keys.
_ALLOWED_GROUP_COL_SQL: dict[str, str] = {
    "soc_code": "jp.soc_code",
    "naics_code": "jp.naics_code",
    "borderplex_subregion": "jp.borderplex_subregion",
    "canonical_role_id": "jp.canonical_role_id",
}

_SALARY_MIDPOINT_EXPR = """(
    CASE
        WHEN nj.salary_min IS NOT NULL AND nj.salary_max IS NOT NULL
            THEN (nj.salary_min::double precision + nj.salary_max::double precision) / 2.0
        WHEN nj.salary_max IS NOT NULL THEN nj.salary_max::double precision
        WHEN nj.salary_min IS NOT NULL THEN nj.salary_min::double precision
        ELSE NULL::double precision
    END
)"""

_ANNUALIZED_SALARY_EXPR = f"""(
    CASE
        WHEN {_SALARY_MIDPOINT_EXPR} IS NULL OR {_SALARY_MIDPOINT_EXPR} <= 0 THEN NULL::double precision
        WHEN LOWER(TRIM(COALESCE(nj.salary_period, ''))) = 'hourly'
            THEN ({_SALARY_MIDPOINT_EXPR}) * 2080.0
        ELSE {_SALARY_MIDPOINT_EXPR}
    END
)"""


def compute_salary_percentiles(
    session: Session,
    group_col: str,
    having_threshold: int = 50,
    *,
    week_start: date | None = None,
) -> dict[str, dict[str, float]]:
    """
    Per-group salary percentiles (p25, p50, p75, p95) using PostgreSQL ``percentile_disc``.

    Joins ``dbo.job_postings`` to ``dbo.normalized_jobs`` on ``source`` + ``external_id``.
    Salary basis: midpoint of min/max when both present, else max, else min, with hourly
    salaries annualized to a 2080-hour year so downstream weekly snapshots stay comparable.

    Groups with fewer than ``having_threshold`` rows are omitted from the result.
    When ``week_start`` is provided, only postings published in that UTC week are included.
    """
    if group_col not in _ALLOWED_GROUP_COL_SQL:
        log.warning(
            "salary_percentiles_invalid_group_col",
            group_col=group_col,
            allowed=tuple(_ALLOWED_GROUP_COL_SQL),
        )
        raise ValueError(f"group_col must be one of {sorted(_ALLOWED_GROUP_COL_SQL)}; got {group_col!r}")

    bind = session.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        log.warning(
            "salary_percentiles_unsupported_dialect",
            dialect=getattr(getattr(bind, "dialect", None), "name", None),
        )
        raise NotImplementedError("compute_salary_percentiles requires PostgreSQL")

    col_sql = _ALLOWED_GROUP_COL_SQL[group_col]
    normalized_threshold = max(int(having_threshold), 0)

    week_filter_sql = ""
    params: dict[str, object] = {"having_threshold": normalized_threshold}
    if week_start is not None:
        week_filter_sql = """
      AND jp.publish_date IS NOT NULL
      AND DATE_TRUNC('week', jp.publish_date AT TIME ZONE 'UTC')::date = :week_start
"""
        params["week_start"] = week_start

    sql = f"""
WITH base AS (
    SELECT
        TRIM(BOTH FROM {col_sql}::text) AS grp,
        {_ANNUALIZED_SALARY_EXPR} AS salary_value
    FROM dbo.job_postings jp
    INNER JOIN dbo.normalized_jobs nj
        ON nj.source = jp.source
        AND nj.external_id = jp.external_id
    WHERE jp.source IS NOT NULL
      AND jp.external_id IS NOT NULL
      AND TRIM(BOTH FROM {col_sql}::text) <> ''
      AND {_ANNUALIZED_SALARY_EXPR} IS NOT NULL
{week_filter_sql}
)
SELECT
    grp,
    COUNT(*)::bigint AS row_count,
    percentile_disc(0.25) WITHIN GROUP (ORDER BY salary_value) AS p25,
    percentile_disc(0.50) WITHIN GROUP (ORDER BY salary_value) AS p50,
    percentile_disc(0.75) WITHIN GROUP (ORDER BY salary_value) AS p75,
    percentile_disc(0.95) WITHIN GROUP (ORDER BY salary_value) AS p95
FROM base
GROUP BY grp
HAVING COUNT(*) >= :having_threshold
"""

    log.info(
        "salary_percentiles_compute_start",
        group_col=group_col,
        having_threshold=normalized_threshold,
        week_start=str(week_start) if week_start else None,
    )

    rows = session.execute(text(sql), params).mappings().all()

    out: dict[str, dict[str, float]] = {}
    for row in rows:
        key = str(row["grp"])
        out[key] = {
            "p25": float(row["p25"]),
            "p50": float(row["p50"]),
            "p75": float(row["p75"]),
            "p95": float(row["p95"]),
        }

    log.info(
        "salary_percentiles_compute_complete",
        group_col=group_col,
        having_threshold=normalized_threshold,
        week_start=str(week_start) if week_start else None,
        group_count=len(out),
    )
    return out
