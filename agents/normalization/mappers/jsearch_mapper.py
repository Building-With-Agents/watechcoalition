"""JSearch field mapper — RawJobRecord (jsearch) to canonical JobRecord.

Zip code resolution: if the posting includes a zip_code, pass it through.
If not but city+state are available, look up postal_geo_data by city+state_code
to resolve the zip. County and other geo data are always looked up via JOIN
to postal_geo_data at query time, never stored on the job record.
"""

from __future__ import annotations

import structlog

from agents.common.types.job_record import JobRecord
from agents.common.types.raw_job_record import RawJobRecord
from agents.normalization.mappers.base import MapperBase

log = structlog.get_logger()


def _resolve_zip_code(city: str | None, state: str | None, raw_zip: str | None) -> str | None:
    """Resolve zip code: use raw value if available, else look up postal_geo_data."""
    if raw_zip:
        return raw_zip.strip()[:10]

    if not city or not state:
        return None

    try:
        from agents.common.data_store.database import check_db_connection, session_scope
        from agents.common.data_store.models import PostalGeoData

        if not check_db_connection():
            return None

        city_clean = city.strip().lower()
        state_clean = state.strip().upper()[:2]

        with session_scope() as session:
            match = (
                session.query(PostalGeoData.zip)
                .filter(
                    PostalGeoData.state_code == state_clean,
                    PostalGeoData.city.ilike(city_clean),
                )
                .first()
            )
            if match:
                return match.zip
    except Exception as exc:
        log.debug("zip_resolution_failed", city=city, state=state, error=str(exc))

    return None


class JSearchMapper(MapperBase):
    """Maps JSearch RawJobRecord to canonical JobRecord."""

    @property
    def mapper_name(self) -> str:
        return "jsearch_mapper"

    def map(self, raw: RawJobRecord) -> JobRecord:
        """Transform a RawJobRecord from JSearch into a JobRecord."""
        zip_code = _resolve_zip_code(raw.city, raw.state, raw.zip_code)

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
            zip_code=zip_code,
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
