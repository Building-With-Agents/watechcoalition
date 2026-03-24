"""Pure helpers for JSearch batch → deterministic enrichment JSONL lines.

Used by ``run_jsearch_enrichment_preview.py`` and unit tests (no DB / I/O).
"""

from __future__ import annotations

from typing import Any

from agents.enrichment.classification import classify_job


def build_extraction_dict(
    skills: Any,
    tools: Any,
    tasks: Any,
    responsibilities: Any,
    context: Any,
) -> dict[str, Any] | None:
    """Build the extraction payload for ``classify_job``, or None if all empty."""
    s, t, ta, r, c = skills or [], tools or [], tasks or [], responsibilities or [], context or []
    if not (s or t or ta or r or c):
        return None
    return {
        "skills": s,
        "tools": t,
        "tasks": ta,
        "responsibilities": r,
        "context": c,
    }


def build_enrichment_output_record(
    *,
    normalized_job_id: int,
    source: str,
    external_id: str,
    job_title: str,
    job_description: str | None,
    skills: Any,
    tools: Any,
    tasks: Any,
    responsibilities: Any,
    context: Any,
    technology_areas: list[tuple[str, str]],
    industry_sectors: list[tuple[str, str]],
    job_posting_id: str | None = None,
    is_internship: bool = False,
) -> dict[str, Any]:
    """Return one JSON-serializable row: ids, source, external_id, seniority, role."""
    extraction = build_extraction_dict(
        skills, tools, tasks, responsibilities, context
    )
    role, seniority = classify_job(
        job_title or "",
        job_description if isinstance(job_description, str) else None,
        extraction,
        technology_areas,
        industry_sectors,
        is_internship=is_internship,
    )
    return {
        "normalized_job_id": normalized_job_id,
        "job_posting_id": job_posting_id,
        "source": source or "",
        "external_id": external_id or "",
        "seniority": seniority,
        "role_classification": role,
    }


NORMALIZED_RUN_SQL = """
WITH latest_ei AS (
    SELECT DISTINCT ON (normalized_job_id)
        normalized_job_id,
        skills,
        tools,
        tasks,
        responsibilities,
        context
    FROM dbo.extracted_intelligence
    WHERE normalized_job_id IS NOT NULL
    ORDER BY normalized_job_id, extracted_at DESC NULLS LAST, id DESC
)
SELECT
    nj.id AS normalized_job_id,
    nj.source,
    nj.external_id,
    nj.title AS job_title,
    nj.company AS job_company,
    nj.description AS job_description,
    nj.city AS job_city,
    nj.state_province AS job_state,
    nj.job_url AS job_url,
    jp.job_posting_id::text AS job_posting_id,
    COALESCE(jp.is_internship, false) AS is_internship,
    le.skills,
    le.tools,
    le.tasks,
    le.responsibilities,
    le.context
FROM dbo.normalized_jobs nj
LEFT JOIN latest_ei le ON le.normalized_job_id = nj.id
LEFT JOIN dbo.job_postings jp
    ON jp.source IS NOT NULL
    AND jp.external_id IS NOT NULL
    AND jp.source = nj.source
    AND jp.external_id = nj.external_id
WHERE nj.ingestion_run_id = :run_id
ORDER BY nj.id
"""
