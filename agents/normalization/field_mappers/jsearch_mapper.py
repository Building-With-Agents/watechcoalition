"""Field mapper for records sourced from JSearch API."""

from __future__ import annotations

from agents.normalization.field_mappers.base_mapper import FieldMapper


class JSearchMapper(FieldMapper):
    """Map JSearch raw fields to canonical normalized fields.

    JSearch records are already mapped to our standard field names by the
    JSearchAdapter in the ingestion layer. This mapper handles any remaining
    transformations or fields that only exist in JSearch payloads.
    """

    def map(self, raw: dict) -> dict:
        payload = raw.get("raw_payload") or {}

        return {
            "external_id": raw.get("external_id", ""),
            "source": "jsearch",
            "title": raw.get("title", ""),
            "company": raw.get("company", ""),
            "location": raw.get("location"),
            "description": raw.get("raw_text", ""),
            "date_posted": raw.get("date_posted"),
            "salary_raw": payload.get("job_salary") or payload.get("job_salary_currency"),
            "employment_type_raw": payload.get("job_employment_type", ""),
        }
