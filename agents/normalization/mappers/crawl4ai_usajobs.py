"""Field mapper for records sourced from Crawl4AI / USAJobs (www.usajobs.gov)."""

from __future__ import annotations

from agents.common.types.job_record import JobRecord
from agents.common.types.raw_job_record import RawJobRecord
from agents.normalization.cleaners import (
    clean_text,
    normalize_date,
    normalize_employment_type,
    parse_salary,
)
from agents.normalization.mappers.base import MapperBase


class Crawl4AIUSAJobsMapper(MapperBase):
    """Map USAJobs (federal) raw fields to canonical normalized fields.

    Uses the same cleaners as :class:`Crawl4AIIndeedMapper`. Federal salary text may
    be a GS scale line (e.g. ``GS-12, Step 1-10``) or a dollar range
    (e.g. ``$80,000 to $104,000 per year``); :func:`parse_salary` extracts numeric
    ranges when present and leaves components None for unrecognized formats.
    Department names in ``raw.company`` are passed through :func:`clean_text`.
    Employment types such as Permanent, Term, Temporary, Seasonal, and Intermittent
    are normalized via :func:`normalize_employment_type`.
    """

    @property
    def mapper_name(self) -> str:
        return "crawl4ai_usajobs_mapper"

    def map(self, raw: RawJobRecord) -> JobRecord:
        salary_data = {}
        if raw.salary_raw:
            salary_data = parse_salary(raw.salary_raw)

        return JobRecord(
            source=raw.source,
            external_id=raw.external_id,
            region_id=raw.region_id,
            title=clean_text(raw.title),
            company=clean_text(raw.company),
            description=clean_text(raw.description),
            job_url=raw.job_url,
            city=raw.city,
            state_province=raw.state,
            country=raw.country,
            is_remote=raw.is_remote,
            date_posted=normalize_date(raw.date_posted.isoformat() if raw.date_posted else None),
            salary_raw=raw.salary_raw,
            salary_min=salary_data.get("salary_min"),
            salary_max=salary_data.get("salary_max"),
            salary_currency=salary_data.get("salary_currency"),
            salary_period=salary_data.get("salary_period"),
            employment_type=normalize_employment_type(raw.employment_type),
            experience_level=raw.experience_level,
            mapper_used=self.mapper_name,
        )
