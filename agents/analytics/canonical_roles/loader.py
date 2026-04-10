"""Load PostingClusterFeatures rows for canonical role clustering."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from agents.analytics.clustering.types import PostingClusterFeatures

log = structlog.get_logger()

_CLUSTERING_LOAD_SQL = """
WITH latest_ei AS (
    SELECT DISTINCT ON (normalized_job_id)
        normalized_job_id,
        skills,
        tools,
        responsibilities,
        context,
        COALESCE(extraction_failed, false) AS extraction_failed
    FROM dbo.extracted_intelligence
    WHERE normalized_job_id IS NOT NULL
    ORDER BY normalized_job_id, extracted_at DESC NULLS LAST, id DESC
)
SELECT
    jp.job_posting_id::text AS job_posting_id,
    jp.job_title AS title,
    jp.company_id::text AS company_id,
    c.company_name AS company_name,
    jp.quality_score AS quality_score,
    nj.experience_level AS seniority,
    le.skills AS skills,
    le.tools AS tools,
    le.responsibilities AS responsibilities
FROM dbo.job_postings jp
INNER JOIN dbo.normalized_jobs nj
    ON jp.source IS NOT NULL
    AND jp.external_id IS NOT NULL
    AND nj.source = jp.source
    AND nj.external_id = jp.external_id
INNER JOIN latest_ei le ON le.normalized_job_id = nj.id
LEFT JOIN dbo.companies c ON c.company_id = jp.company_id
WHERE jp.company_id IS NOT NULL
    AND COALESCE(jp.is_duplicate, false) = false
    AND (jp.is_spam IS NOT TRUE)
    AND (jp.spam_score IS NULL OR jp.spam_score < 0.9)
    AND le.extraction_failed = false
    {week_filter}
ORDER BY jp.job_posting_id
{limit_clause}
"""


def _skill_or_tool_label(item: Mapping[str, Any] | Any) -> str | None:
    if not isinstance(item, Mapping):
        return None
    name = item.get("skill_name") or item.get("tool_name") or item.get("label") or item.get("name")
    if name is None:
        return None
    text = str(name).strip()
    return text or None


def _responsibility_text(item: Mapping[str, Any] | Any) -> str | None:
    if not isinstance(item, Mapping):
        return None
    for key in ("responsibility_description", "text", "description", "label"):
        raw = item.get(key)
        if raw is not None:
            t = str(raw).strip()
            if t:
                return t
    return None


def _parse_string_list_column(raw: Any, *, extractor: Any) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        label = extractor(item)
        if label and label not in seen:
            seen.add(label)
            out.append(label)
    return out


def _row_to_features(row: Mapping[str, Any]) -> PostingClusterFeatures:
    skills = _parse_string_list_column(row.get("skills"), extractor=_skill_or_tool_label)
    tools = _parse_string_list_column(row.get("tools"), extractor=_skill_or_tool_label)
    responsibilities = _parse_string_list_column(
        row.get("responsibilities"),
        extractor=_responsibility_text,
    )

    q = row.get("quality_score")
    quality: float | None
    if q is None:
        quality = None
    else:
        try:
            quality = float(q)
        except (TypeError, ValueError):
            quality = None

    seniority_raw = row.get("seniority")
    seniority = str(seniority_raw).strip() if seniority_raw is not None else None
    if seniority == "":
        seniority = None

    company_id = row.get("company_id")
    company_name = row.get("company_name")
    emp_id = str(company_id).strip() if company_id is not None else None
    emp_name = str(company_name).strip() if company_name is not None else None
    if emp_id == "":
        emp_id = None
    if emp_name == "":
        emp_name = None

    return PostingClusterFeatures(
        posting_id=str(row["job_posting_id"]).strip(),
        title=str(row["title"] or "").strip() or "(untitled)",
        skills=skills,
        tools=tools,
        responsibilities=responsibilities,
        seniority=seniority,
        employer_id=emp_id,
        employer_name=emp_name,
        quality_score=quality,
    )


def load_posting_cluster_features(
    session: Session,
    *,
    week_start: date | None = None,
    limit: int | None = None,
) -> list[PostingClusterFeatures]:
    """Load survivor postings with extraction for clustering.

    Filters: company_id present, not duplicate, not spam auto-reject, successful extraction.
    CLUSTER_MIN_TOTAL_POSTINGS is enforced downstream in the clustering pipeline.

    When ``week_start`` is set (ISO week Monday, UTC boundary), only rows whose
    ``publish_date`` falls in that calendar week are included.

    ``CLUSTER_MIN_TOTAL_POSTINGS`` (default 500) applies only inside the clustering
    package; the global analytics #179 50-posting guard is not implemented here.
    """
    week_filter = ""
    params: dict[str, Any] = {}
    if week_start is not None:
        week_filter = (
            " AND jp.publish_date IS NOT NULL "
            "AND (DATE_TRUNC('week', jp.publish_date AT TIME ZONE 'UTC')::date) = :week_start "
        )
        params["week_start"] = week_start

    limit_clause = ""
    if limit is not None and limit > 0:
        limit_clause = " LIMIT :load_limit "
        params["load_limit"] = limit

    sql = text(_CLUSTERING_LOAD_SQL.format(week_filter=week_filter, limit_clause=limit_clause))
    result = session.execute(sql, params)
    rows = result.mappings().all()
    features = [_row_to_features(dict(r)) for r in rows]
    log.info(
        "clustering_features_loaded",
        row_count=len(features),
        week_start=str(week_start) if week_start else None,
        limit=limit,
    )
    return features
