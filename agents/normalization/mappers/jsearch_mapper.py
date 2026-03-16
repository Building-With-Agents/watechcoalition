"""JSearch field mapper — RawJobRecord (jsearch) to canonical JobRecord."""

from __future__ import annotations

from agents.common.types.job_record import JobRecord
from agents.common.types.raw_job_record import RawJobRecord
from agents.normalization.mappers.base import MapperBase


class JSearchMapper(MapperBase):
    """Maps JSearch RawJobRecord to canonical JobRecord."""

    @property
    def mapper_name(self) -> str:
        return "jsearch_mapper"

    def map(self, raw: RawJobRecord) -> JobRecord:
        """Transform a RawJobRecord from JSearch into a JobRecord."""
        return JobRecord(
            raw_job_id=0,
            ingestion_run_id="",
            region_id=raw.region_id or "",
            source=raw.source,
            external_id=raw.external_id,
            title=raw.title.strip() or "Untitled",
            company=raw.company.strip() or "Unknown",
            description=raw.description or None,
            job_url=raw.job_url,
            city=raw.city,
            state_province=raw.state,
            country=raw.country,
            work_arrangement=None,
            is_remote=raw.is_remote,
            date_posted=raw.date_posted,
            salary_raw=raw.salary_raw,
            salary_min=raw.salary_min,
            salary_max=raw.salary_max,
            salary_currency=raw.salary_currency,
            salary_period=raw.salary_period,
            employment_type=raw.employment_type,
            experience_level=raw.experience_level,
            occupation_code=None,
            mapper_used=self.mapper_name,
        )
