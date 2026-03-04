"""Field mapper for records sourced from Crawl4AI / web scraping / fixture fallback."""

from __future__ import annotations

from agents.normalization.field_mappers.base_mapper import FieldMapper


class ScraperMapper(FieldMapper):
    """Map crawl4ai / web_scrape raw fields to canonical normalized fields."""

    def map(self, raw: dict) -> dict:
        return {
            "external_id": raw.get("external_id", ""),
            "source": raw.get("source", "crawl4ai"),
            "title": raw.get("title", ""),
            "company": raw.get("company", ""),
            "location": raw.get("location"),
            "description": raw.get("raw_text", ""),
            "date_posted": raw.get("date_posted") or raw.get("timestamp"),
            "salary_raw": None,  # fixture data has no salary field
            "employment_type_raw": "",
        }
