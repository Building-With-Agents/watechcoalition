"""Field completeness scoring for fuzzy dedup survivor arbitration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

# Plan: salary > location > description richness; recency tie-breaker
_WEIGHT_SALARY = 40
_WEIGHT_LOCATION = 30
_WEIGHT_DESC = 20


def completeness_score(row: dict[str, Any]) -> int:
    """
    Higher = richer structured data for downstream analytics.

    Uses only non-PII structural signals already on job_postings.
    """
    score = 0
    salary = row.get("salary_range")
    if salary is not None and str(salary).strip():
        score += _WEIGHT_SALARY

    loc = row.get("location")
    z = row.get("zip")
    county = row.get("county")
    if (loc and str(loc).strip()) or (z and str(z).strip()) or (county and str(county).strip()):
        score += _WEIGHT_LOCATION

    desc = row.get("job_description") or ""
    if isinstance(desc, str):
        ld = len(desc.strip())
        score += min(_WEIGHT_DESC, ld // 100)

    return score


def publish_date_for_tiebreak(row: dict[str, Any]) -> datetime | None:
    """Newer wins when completeness ties."""
    pd = row.get("publish_date")
    if pd is None:
        return None
    if isinstance(pd, datetime):
        return pd
    return None
