"""Crawl4AI adapter for USAJobs federal job listings.

Builds a USAJobs search URL from ``RegionConfig``, scrapes the results
page via Crawl4AI ``AsyncWebCrawler``, and parses structured job fields
from the HTML.

Source key: ``crawl4ai_usajobs``
"""

from __future__ import annotations

import re
from urllib.parse import quote_plus

import structlog

from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.base_adapter import SourceAdapter

log = structlog.get_logger()


def _build_usajobs_url(region: RegionConfig) -> str:
    """Build a USAJobs search URL from region config."""
    keywords = " ".join(region.keywords) if region.keywords else "software engineer"
    location = region.query_location or "Washington"
    return (
        f"https://www.usajobs.gov/Search/Results"
        f"?k={quote_plus(keywords)}&l={quote_plus(location)}"
    )


def _extract_jobs_from_html(html: str, region_id: str) -> list[RawJobRecord]:
    """Parse USAJobs HTML to extract job listing cards.

    USAJobs uses a structured card layout with specific CSS classes
    and data attributes.  This parser extracts available fields.
    """
    records: list[RawJobRecord] = []

    # USAJobs uses <div class="usajobs-search-result--core"> or similar
    # Each result has a control number, title, department, location, salary
    control_pattern = re.compile(
        r'data-control-number="(\d+)"',
        re.DOTALL,
    )
    title_pattern = re.compile(
        r'class="[^"]*usajobs-search-result--item__title[^"]*"[^>]*>'
        r'\s*<a[^>]*>([^<]+)',
        re.DOTALL,
    )
    department_pattern = re.compile(
        r'class="[^"]*usajobs-search-result--item__department[^"]*"[^>]*>'
        r'\s*([^<]+)',
        re.DOTALL,
    )
    location_pattern = re.compile(
        r'class="[^"]*usajobs-search-result--item__location[^"]*"[^>]*>'
        r'\s*([^<]+)',
        re.DOTALL,
    )
    salary_pattern = re.compile(
        r'class="[^"]*usajobs-search-result--item__salary[^"]*"[^>]*>'
        r'\s*([^<]+)',
        re.DOTALL,
    )
    date_pattern = re.compile(
        r'class="[^"]*usajobs-search-result--item__closing-date[^"]*"[^>]*>'
        r'[^<]*<time[^>]*datetime="([^"]*)"',
        re.DOTALL,
    )

    control_numbers = control_pattern.findall(html)
    titles = title_pattern.findall(html)
    departments = department_pattern.findall(html)
    locations = location_pattern.findall(html)
    salaries = salary_pattern.findall(html)
    dates = date_pattern.findall(html)

    for i, control_num in enumerate(control_numbers):
        if not control_num:
            continue

        title = titles[i].strip() if i < len(titles) else ""
        department = departments[i].strip() if i < len(departments) else ""
        location_text = locations[i].strip() if i < len(locations) else ""
        salary_raw = salaries[i].strip() if i < len(salaries) else None

        # Parse city/state from location text (e.g. "Seattle, Washington")
        city, state = None, None
        if location_text:
            parts = [p.strip() for p in location_text.split(",")]
            if len(parts) >= 2:
                city = parts[0]
                state = parts[1]
            elif len(parts) == 1:
                city = parts[0]

        # Check for remote/telework indicators
        is_remote = None
        if location_text and any(
            kw in location_text.lower()
            for kw in ("remote", "telework", "anywhere")
        ):
            is_remote = True

        job_url = f"https://www.usajobs.gov/job/{control_num}"

        records.append(
            RawJobRecord(
                external_id=f"usajobs-{control_num}",
                source="crawl4ai_usajobs",
                region_id=region_id,
                title=title,
                company=department,  # Federal department is the "company"
                description="",  # Requires visiting individual listing
                city=city,
                state=state,
                country="US",
                is_remote=is_remote,
                salary_raw=salary_raw,
                employment_type="FULLTIME",  # Federal jobs are typically full-time
                job_url=job_url,
                raw_payload={
                    "control_number": control_num,
                    "department": department,
                    "location_text": location_text,
                },
            )
        )

    return records


class Crawl4AIUSAJobsAdapter(SourceAdapter):
    """Fetches federal job postings from USAJobs via Crawl4AI web scraping."""

    @property
    def source_name(self) -> str:
        return "crawl4ai_usajobs"

    async def fetch(self, region: RegionConfig) -> list[RawJobRecord]:
        """Fetch job postings from USAJobs for the given region."""
        url = _build_usajobs_url(region)

        try:
            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)

                if not result.success:
                    log.warning(
                        "crawl4ai_usajobs_fetch_failed",
                        url=url,
                        error="Crawl unsuccessful",
                    )
                    return []

                html = result.html or ""
                records = _extract_jobs_from_html(html, region.region_id)

                log.info(
                    "crawl4ai_usajobs_fetch_complete",
                    count=len(records),
                    url=url,
                )
                return records

        except ImportError:
            log.warning(
                "crawl4ai_not_installed",
                note="pip install crawl4ai to enable USAJobs scraping",
            )
            return []
        except Exception as exc:
            log.warning("crawl4ai_usajobs_error", url=url, error=str(exc))
            return []

    async def health_check(self) -> dict:
        """Return adapter readiness status."""
        try:
            import crawl4ai  # noqa: F401
            reachable = True
        except ImportError:
            reachable = False

        return {"reachable": reachable, "source": self.source_name}
