"""Crawl4AI source adapter — City of El Paso GovernmentJobs portal.

Contract: implements SourceAdapter. Output is list[RawJobRecord].
Target: https://www.governmentjobs.com/careers/elpaso (U.S. only, El Paso TX).
Lead note: Crawl4AI tends to work better on .gov sites; may break on sites like Indeed.

Region behavior:
  RegionConfig is accepted per SourceAdapter contract; region_id is used in output.
  This source uses a single fixed target (El Paso portal) and does not apply
  Las Cruces-specific or other region filtering. Scope is U.S.-only by source choice.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.base_adapter import SourceAdapter


class Crawl4AIAdapterError(Exception):
    """Raised when the adapter encounters an unrecoverable failure."""

    pass


# Minimum HTML length to consider page content valid (avoids empty/broken responses).
_MIN_HTML_LEN = 500

# Single target: City of El Paso careers portal (GovernmentJobs/NEOGOV).
# U.S.-only by source choice. Las Cruces and other regions are not directly
# supported; region_id from RegionConfig is passed through for output metadata only.
EL_PASO_PORTAL_BASE = "https://www.governmentjobs.com"
EL_PASO_CAREERS_URL = "https://www.governmentjobs.com/careers/elpaso"
TEST_URL = "https://bebee.com/us/jobs"

# GovernmentJobs "no openings" signal (e.g. "0 jobs found", "no jobs available").
_NO_OPENINGS_RE = re.compile(
    r"\b(0\s*jobs?\s*found|no\s+jobs?\s*(available|posted|open)|no\s+openings)\b",
    re.I,
)

# Job links: /careers/elpaso/jobs/5257914/construction-inspector or /jobs/5257914
_JOB_LINK_RE = re.compile(
    r'href=["\']([^"\']*?/careers/elpaso/jobs/(\d+)(/[^"\']*)?)["\']',
    re.I,
)


def _normalize_str(s: str) -> str:
    """Trim and collapse internal whitespace; avoid newline-heavy strings."""
    if not s:
        return ""
    return " ".join(s.split()).strip()


def _normalize_url(path: str, base: str) -> str:
    """Return absolute URL; path may be relative or absolute."""
    if not path:
        return ""
    s = path.strip()
    if s.startswith("http://") or s.startswith("https://"):
        return s
    base = base.rstrip("/")
    return f"{base}/{s.lstrip('/')}"


class Crawl4AIAdapter(SourceAdapter):
    """Concrete adapter for Crawl4AI — El Paso GovernmentJobs portal."""

    def __init__(self, target_urls: list[str] | None = None) -> None:
        # Allow override for testing; default uses fixed El Paso portal.
        self._target_urls = target_urls or [TEST_URL]

    @property
    def source_name(self) -> str:
        return "crawl4ai"

    def _build_search_url(self, region: RegionConfig) -> str:
        """Return the crawl target URL. Single target: El Paso portal."""
        return self._target_urls[0] if self._target_urls else TEST_URL

    def _extract_job_cards(self, html: str, base_url: str) -> list[dict]:
        """Extract job links from HTML. Returns list of {external_id, title, job_url}."""
        if not html:
            return []
        jobs: list[dict] = []
        seen_ids: set[str] = set()
        for m in _JOB_LINK_RE.finditer(html):
            path, job_id, slug_part = m.group(1), m.group(2), m.group(3) or ""
            slug = slug_part.lstrip("/") if slug_part else ""
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)
            job_url = _normalize_url(path, base_url)
            title = _normalize_str(
                slug.replace("-", " ").title() if slug else f"Job {job_id}"
            )
            jobs.append({"external_id": job_id.strip(), "title": title, "job_url": job_url})
        return jobs

    def _to_raw_job_record(
        self,
        card: dict,
        region: RegionConfig,
        index: int,
    ) -> RawJobRecord:
        """Map extracted card to RawJobRecord. Minimal and strict: only populate
        fields we can extract confidently; set unavailable fields to None.
        """
        external_id = _normalize_str(str(card.get("external_id", str(index))))
        title = _normalize_str(str(card.get("title", "Unknown")))
        job_url = _normalize_url(str(card.get("job_url", "")), EL_PASO_PORTAL_BASE)
        company = _normalize_str("City of El Paso")  # Portal employer
        region_id = _normalize_str(region.region_id)
        raw_hash = hashlib.sha256(
            f"crawl4ai|{external_id}|{title}|{job_url}".encode()
        ).hexdigest()
        payload = {"external_id": external_id, "title": title, "job_url": job_url}
        return RawJobRecord(
            external_id=external_id,
            source="crawl4ai",
            region_id=region_id,
            raw_payload_hash=raw_hash,
            title=title,
            company=company,
            description="",
            city=None,
            state=None,
            country=None,
            is_remote=None,
            date_posted=None,
            date_ingested=datetime.utcnow(),
            salary_raw=None,
            salary_min=None,
            salary_max=None,
            salary_currency=None,
            salary_period=None,
            employment_type=None,
            experience_level=None,
            job_url=job_url or None,
            source_url=EL_PASO_PORTAL_BASE,
            raw_payload=payload,
        )

    async def fetch(self, region: RegionConfig) -> list[RawJobRecord]:
        """Fetch raw job records from El Paso GovernmentJobs portal.

        Raises:
            Crawl4AIAdapterError: When target is unreachable, Crawl4AI fails,
                page content is empty/unexpected, or large page has zero job links
                without an explicit "no openings" signal (possible parser breakage).
        Returns:
            list[RawJobRecord]: Non-empty when jobs found; empty only when
                page contains an explicit "no jobs / no openings" signal.
        """
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

        url = self._build_search_url(region)

        try:
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                result = await crawler.arun(
                    url,
                    config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
                )
        except Exception as e:
            raise Crawl4AIAdapterError(f"Crawl4AI init/fetch failed: {e}") from e

        # has_html = getattr(result, "html", None) is not None
        # has_cleaned = getattr(result, "cleaned_html", None) is not None

        if not result.success:
            msg = getattr(result, "error_message", str(result)) or "unknown"
            raise Crawl4AIAdapterError(f"Target unreachable: {msg}")

        html = getattr(result, "html", None) or getattr(result, "cleaned_html", None)
        if html is None:
            raise Crawl4AIAdapterError("Crawl result missing html and cleaned_html")
        html = str(html) if html else ""

        if len(html) < _MIN_HTML_LEN:
            raise Crawl4AIAdapterError(f"Page content too small ({len(html)} chars)")

        # job_match_count = len(list(_JOB_LINK_RE.finditer(html)))
        no_openings_m = _NO_OPENINGS_RE.search(html)
        no_openings_matched = no_openings_m is not None
        cards = self._extract_job_cards(html, EL_PASO_PORTAL_BASE)

        def _debug_save_html() -> None:
            try:
                with open("debug_elpaso_page.html", "w", encoding="utf-8") as f:
                    f.write(html)
            except OSError :
                # print(f"[DEBUG fetch] could not save HTML: {e}")
                pass

        if not cards and len(html) >= _MIN_HTML_LEN:
            if no_openings_matched:
                # _debug_save_html()
                return []
            # _debug_save_html()
            raise Crawl4AIAdapterError(
                "Large page with zero job links; possible parser breakage"
            )
        records: list[RawJobRecord] = []
        for i, card in enumerate(cards):
            records.append(self._to_raw_job_record(card, region, i))
        return records

    async def health_check(self) -> dict:
        """Probe adapter state and El Paso portal reachability.

        Returns a dict with:
            initialized (bool): True after __init__.
            target_configured (bool): True when a target URL is set.
            reachable (bool): True when the crawl succeeded (target responded).
            extractable_structure (bool): True when crawl succeeded, HTML is present,
                and HTML contains the expected job-link pattern or no-openings signal.
            status (str): "operational" when reachable and extractable_structure;
                "reachable_but_unextractable" when reachable but structure not detected;
                "crawl_failed" when result.success is False; "error" when an exception is raised.
            source (str): "crawl4ai".
            error (str | None): None when status is "operational"; otherwise a
                short message describing the failure.
        """
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
        target = self._target_urls[0] if self._target_urls else EL_PASO_PORTAL_BASE
        try:
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                result = await crawler.arun(
                    target,
                    config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
                )
            success = getattr(result, "success", False)
            html = getattr(result, "html", None) or getattr(result, "cleaned_html", None)
            html_str = str(html) if html else ""
            extractable = bool(
                success
                and html_str
                and (_JOB_LINK_RE.search(html_str) or _NO_OPENINGS_RE.search(html_str))
            )
            if success:
                status = "operational" if extractable else "reachable_but_unextractable"
                error = None if extractable else "Expected job-link or no-openings pattern not found"
            else:
                status = "crawl_failed"
                error = getattr(result, "error_message", "unknown")
            return {
                "initialized": True,
                "target_configured": bool(self._target_urls),
                "reachable": success,
                "extractable_structure": extractable,
                "status": status,
                "source": self.source_name,
                "error": error,
            }
        except Exception as e:
            return {
                "initialized": True,
                "target_configured": bool(self._target_urls),
                "reachable": False,
                "extractable_structure": False,
                "status": "error",
                "source": self.source_name,
                "error": str(e),
            }
