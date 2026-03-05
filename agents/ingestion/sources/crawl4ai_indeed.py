"""Crawl4AI adapter for Indeed job listings.

Builds an Indeed search URL from ``RegionConfig`` (keywords + query_location),
scrapes the results page via Crawl4AI ``AsyncWebCrawler``, and parses
structured job fields from the HTML.

Source key: ``crawl4ai_indeed``
"""

from __future__ import annotations

import re
from urllib.parse import quote_plus

import structlog

from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.base_adapter import SourceAdapter

log = structlog.get_logger()


def _build_indeed_url(region: RegionConfig) -> str:
    """Build an Indeed search URL from region config."""
    keywords = " ".join(region.keywords) if region.keywords else "software engineer"
    location = region.query_location or "Washington state"
    return f"https://www.indeed.com/jobs?q={quote_plus(keywords)}&l={quote_plus(location)}"


def _extract_jobs_from_html(html: str, region_id: str) -> list[RawJobRecord]:
    """Parse Indeed HTML to extract job cards.

    Indeed's HTML structure uses data attributes and specific CSS classes
    for job cards.  This parser extracts what it can and returns partial
    records — the normalization layer fills gaps.
    """
    records: list[RawJobRecord] = []

    # Indeed wraps each result in a div with class "job_seen_beacon" or
    # a <td> with class "resultContent".  We use regex-based extraction
    # as a lightweight alternative to a full HTML parser.
    # Pattern: find job card blocks
    card_pattern = re.compile(
        r'data-jk="([^"]*)"',
        re.DOTALL,
    )
    title_pattern = re.compile(
        r'<span[^>]*id="jobTitle-[^"]*"[^>]*>(?:<span[^>]*>)?([^<]+)',
        re.DOTALL,
    )
    company_pattern = re.compile(
        r'data-testid="company-name"[^>]*>([^<]+)',
        re.DOTALL,
    )
    location_pattern = re.compile(
        r'data-testid="text-location"[^>]*>([^<]+)',
        re.DOTALL,
    )
    salary_pattern = re.compile(
        r'class="[^"]*salary-snippet[^"]*"[^>]*>([^<]+)',
        re.DOTALL,
    )

    # Extract all job keys first
    job_keys = card_pattern.findall(html)
    titles = title_pattern.findall(html)
    companies = company_pattern.findall(html)
    locations = location_pattern.findall(html)
    salaries = salary_pattern.findall(html)

    # Zip through available data — some fields may be shorter
    for i, jk in enumerate(job_keys):
        if not jk:
            continue

        title = titles[i].strip() if i < len(titles) else ""
        company = companies[i].strip() if i < len(companies) else ""
        location_text = locations[i].strip() if i < len(locations) else ""
        salary_raw = salaries[i].strip() if i < len(salaries) else None

        # Parse city/state from location text (e.g. "Seattle, WA")
        city, state = None, None
        if location_text:
            parts = [p.strip() for p in location_text.split(",")]
            if len(parts) >= 2:
                city = parts[0]
                state = parts[1]
            elif len(parts) == 1:
                city = parts[0]

        is_remote = None
        if location_text and "remote" in location_text.lower():
            is_remote = True

        job_url = f"https://www.indeed.com/viewjob?jk={jk}"

        records.append(
            RawJobRecord(
                external_id=f"indeed-{jk}",
                source="crawl4ai_indeed",
                region_id=region_id,
                title=title,
                company=company,
                description="",  # Description requires visiting individual job page
                city=city,
                state=state,
                country="US",
                is_remote=is_remote,
                salary_raw=salary_raw,
                job_url=job_url,
                raw_payload={"job_key": jk, "location_text": location_text},
            )
        )

    return records


class Crawl4AIIndeedAdapter(SourceAdapter):
    """Fetches job postings from Indeed via Crawl4AI web scraping."""

    @property
    def source_name(self) -> str:
        return "crawl4ai_indeed"

    async def fetch(self, region: RegionConfig) -> list[RawJobRecord]:
        """Fetch job postings from Indeed for the given region."""
        url = _build_indeed_url(region)

        try:
            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)

                if not result.success:
                    log.warning(
                        "crawl4ai_indeed_fetch_failed",
                        url=url,
                        error="Crawl unsuccessful",
                    )
                    return []

                html = result.html or ""
                records = _extract_jobs_from_html(html, region.region_id)

                log.info(
                    "crawl4ai_indeed_fetch_complete",
                    count=len(records),
                    url=url,
                )
                return records

        except ImportError:
            log.warning(
                "crawl4ai_not_installed",
                note="pip install crawl4ai to enable Indeed scraping",
            )
            return []
        except Exception as exc:
            log.warning("crawl4ai_indeed_error", url=url, error=str(exc))
            return []

    async def health_check(self) -> dict:
        """Return adapter readiness status."""
        try:
            import crawl4ai  # noqa: F401
            reachable = True
        except ImportError:
            reachable = False

        return {"reachable": reachable, "source": self.source_name}
