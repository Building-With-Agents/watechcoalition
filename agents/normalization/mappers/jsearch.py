"""Field mapper for records sourced from JSearch API."""

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


class JSearchMapper(MapperBase):
    """Map JSearch raw fields to canonical normalized fields.

    Applies cleaners to produce a validated ``JobRecord``.
    """

    @property
    def mapper_name(self) -> str:
        return "jsearch_mapper"

    def map(self, raw: RawJobRecord) -> JobRecord:
        # Parse salary from raw string if structured salary fields are absent
        salary_data = {}
        if raw.salary_min is not None or raw.salary_max is not None:
            salary_data = {
                "salary_min": raw.salary_min,
                "salary_max": raw.salary_max,
                "salary_currency": raw.salary_currency or "USD",
                "salary_period": raw.salary_period or "annual",
            }
        elif raw.salary_raw:
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
