"""Query ``dbo.job_postings`` rows that are not yet tied to ``extracted_intelligence``.

``extracted_intelligence`` keys off ``normalized_job_id`` (integer), not ``job_posting_id``.
The bridge used here matches production-style linkage: when a normalized row represents a
seeded posting, ``normalized_jobs.external_id`` equals ``job_postings.job_posting_id``.

A posting is **excluded** if there is any ``extracted_intelligence`` row joined to
``normalized_jobs`` where ``LOWER(TRIM(nj.external_id)) = LOWER(TRIM(jp.job_posting_id))``.

Usage (read-only)::

    from sqlalchemy import create_engine, text
    from agents.tests.support.job_posting_extraction_query import (
        fetch_unextracted_job_posting_rows,
        row_to_job_record,
    )

    with engine.connect() as conn:
        rows = fetch_unextracted_job_posting_rows(conn, limit=20)
        jobs = [row_to_job_record(r) for r in rows]
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from agents.common.types import JobRecord

# Default band for "10–20 records" sampling in tests and scripts.
DEFAULT_MIN_SAMPLE = 15
DEFAULT_MAX_SAMPLE = 20

_SQL = """
SELECT
    jp.job_posting_id,
    jp.job_title,
    jp.job_description,
    jp.job_post_url,
    jp.employment_type,
    jp.location::text AS location,
    c.company_name
FROM dbo.job_postings jp
INNER JOIN dbo.companies c ON c.company_id = jp.company_id
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.extracted_intelligence ei
    INNER JOIN dbo.normalized_jobs nj ON nj.id = ei.normalized_job_id
    WHERE LOWER(TRIM(COALESCE(nj.external_id, ''))) = LOWER(TRIM(COALESCE(jp.job_posting_id, '')))
)
AND jp.job_title IS NOT NULL
AND TRIM(jp.job_title) <> ''
AND jp.job_description IS NOT NULL
AND LENGTH(TRIM(jp.job_description)) >= 20
ORDER BY jp.publish_date DESC NULLS LAST, jp.job_posting_id
LIMIT :lim
"""


def fetch_unextracted_job_posting_rows(conn: Connection, *, limit: int = DEFAULT_MAX_SAMPLE) -> list[dict[str, Any]]:
    """Return up to ``limit`` job posting rows with company name, none with completed extraction linkage."""
    rows = conn.execute(text(_SQL), {"lim": limit}).mappings().all()
    return [dict(r) for r in rows]


def row_to_job_record(row: Mapping[str, Any]) -> JobRecord:
    """Map a query row to :class:`JobRecord` for skills extractors."""
    title = (row.get("job_title") or "").strip()
    company = (row.get("company_name") or "Unknown").strip() or "Unknown"
    desc = (row.get("job_description") or "").strip()
    pid = str(row.get("job_posting_id") or "").strip()
    if not pid:
        raise ValueError("job_posting_id is required")
    jurl = row.get("job_post_url")
    emp = row.get("employment_type")
    loc = row.get("location")
    return JobRecord(
        source="job_postings",
        external_id=pid,
        ingestion_run_id="db-job-posting-sample",
        title=title,
        company=company,
        description=desc or None,
        employment_type=str(emp).strip() if emp else None,
        job_url=str(jurl).strip() if jurl else None,
        city=None,
        state_province=None,
        country=None,
        location=str(loc).strip() if loc else None,
        mapper_used="job_posting_extraction_query",
    )
