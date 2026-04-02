"""Crawl4AI source adapter — USAJobs federal jobs portal (www.usajobs.gov).

Contract: implements SourceAdapter. Output is list[RawJobRecord].
Target: https://www.usajobs.gov/Search/Results (Angular SPA; requires JS wait).

Region behavior:
  Search URL is built from RegionConfig.keywords (k) and RegionConfig.query_location (l).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import structlog

from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.base_adapter import SourceAdapter

log = structlog.get_logger()


class Crawl4AIUSAJobsAdapterError(Exception):
    """Raised when the adapter encounters an unrecoverable failure."""

    pass


# Minimum HTML length to consider page content valid (avoids empty/broken responses).
_MIN_HTML_LEN = 500

USAJOBS_BASE = "https://www.usajobs.gov"
USAJOBS_SEARCH_BASE = f"{USAJOBS_BASE}/Search/Results"

# Absolute job URLs from rendered search results.
_JOB_URL_FULL_RE = re.compile(
    r"https://www\.usajobs\.gov/job/(\d+)/([^\s\"\'<>]*)",
    re.I,
)
# Relative /job/... links (Angular may emit these).
_JOB_URL_REL_RE = re.compile(
    r"href=[\"'](/job/(\d+)/[^\"']+)[\"']",
    re.I,
)

_NO_RESULTS_RE = re.compile(
    r"\b(no\s+jobs?\s+found|couldn't\s+find\s+any\s+results|please\s+refine\s+your\s+search)\b",
    re.I,
)

_EMPLOYMENT_FALLBACK_RE = re.compile(
    r"\b(full[- ]time|part[- ]time|multiple\s+schedules|shift\s+work|intermittent|job\s+sharing)\b",
    re.I,
)

_SALARY_FALLBACK_RE = re.compile(
    r"\$[\d,]+(?:\s*-\s*\$?[\d,]+)?(?:\s*/\s*(?:year|yr|hour|hr|annually|per\s+hour))?",
    re.I,
)

_CITY_STATE_RE = re.compile(
    r"\b([A-Za-z][A-Za-z\s\.\-]+),\s*([A-Z]{2})\b",
)


def _normalize_str(s: str) -> str:
    """Trim and collapse internal whitespace."""
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


def _title_from_slug(slug: str) -> str:
    """Derive a display title from the URL slug segment after the job id."""
    slug = (slug or "").strip("/")
    if not slug:
        return ""
    return _normalize_str(slug.replace("-", " ").title())


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags; collapse whitespace (no external deps)."""
    if not html:
        return ""
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return _normalize_str(text)


def _spa_crawl_config() -> Any:
    """SPA requires delayed JS execution before HTML is populated."""
    from crawl4ai import CacheMode, CrawlerRunConfig

    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        js_code="await new Promise(r => setTimeout(r, 5000));",
        delay_before_return_html=2.0,
    )


def _parse_ld_json_jobposting(html: str) -> dict[str, Any] | None:
    """Extract first JobPosting object from application/ld+json, if present."""
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',
        html,
        re.I,
    ):
        raw = m.group(1).strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            types = item.get("@type")
            ok = types == "JobPosting" or (isinstance(types, list) and "JobPosting" in types)
            if ok:
                return item
    return None


def _ld_salary_raw(ld: dict[str, Any]) -> str | None:
    bs = ld.get("baseSalary")
    if isinstance(bs, dict):
        val = bs.get("value")
        if isinstance(val, dict):
            lo = val.get("minValue")
            hi = val.get("maxValue")
            unit = val.get("unitText") or ""
            if lo is not None and hi is not None:
                return _normalize_str(f"${lo} - ${hi} {unit}".strip())
            if lo is not None:
                return _normalize_str(f"${lo} {unit}".strip())
        if isinstance(bs, str):
            return _normalize_str(bs)
    return None


def _ld_location_city_state(ld: dict[str, Any]) -> tuple[str | None, str | None]:
    jl = ld.get("jobLocation")
    if isinstance(jl, list) and jl:
        jl = jl[0]
    if not isinstance(jl, dict):
        return None, None
    addr = jl.get("address")
    if not isinstance(addr, dict):
        return None, None
    city = addr.get("addressLocality")
    state = addr.get("addressRegion")
    c = _normalize_str(str(city)) if city else None
    s = _normalize_str(str(state)) if state else None
    if s and len(s) == 2:
        return c, s.upper()
    return c, s


def _normalize_employment_type(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip().lower()
    if "full" in s and "time" in s:
        return "Full-time"
    if "part" in s and "time" in s:
        return "Part-time"
    if "contract" in s:
        return "Contract"
    if "intermittent" in s:
        return "Intermittent"
    return _normalize_str(raw) or None


def _parse_detail_fields_from_ld(ld: dict[str, Any]) -> dict[str, Any]:
    """Map schema.org JobPosting JSON-LD to our detail field dict."""
    desc = ld.get("description")
    description = _strip_html_tags(desc) if isinstance(desc, str) else ""

    org = ld.get("hiringOrganization")
    company = ""
    if isinstance(org, dict):
        company = _normalize_str(str(org.get("name") or ""))

    et_raw = ld.get("employmentType")
    if isinstance(et_raw, list) and et_raw:
        et_raw = et_raw[0]
    employment_type = None
    if isinstance(et_raw, str):
        employment_type = _normalize_employment_type(et_raw)

    city, state = _ld_location_city_state(ld)
    salary_raw = _ld_salary_raw(ld)

    title = ld.get("title")
    title_s = _normalize_str(str(title)) if title else ""

    return {
        "description": description,
        "salary_raw": salary_raw,
        "employment_type": employment_type,
        "city": city,
        "state": state,
        "company": company,
        "title": title_s,
    }


def _parse_detail_fields_fallback(html: str) -> dict[str, Any]:
    """Regex / text heuristics when JSON-LD is missing."""
    text = _strip_html_tags(html)
    salary_raw = None
    sm = _SALARY_FALLBACK_RE.search(text)
    if sm:
        salary_raw = _normalize_str(sm.group(0))

    employment_type = None
    em = _EMPLOYMENT_FALLBACK_RE.search(text)
    if em:
        employment_type = _normalize_str(em.group(1)).title()

    city, state = None, None
    cm = _CITY_STATE_RE.search(text)
    if cm:
        city = _normalize_str(cm.group(1))
        state = cm.group(2).upper()

    # Longest paragraph-ish block as description fallback
    description = text[:12000] if len(text) > 200 else text

    return {
        "description": description,
        "salary_raw": salary_raw,
        "employment_type": employment_type,
        "city": city,
        "state": state,
        "company": "",
        "title": "",
    }


def _parse_detail_html(html: str) -> dict[str, Any]:
    """Extract detail fields from a job announcement HTML page."""
    ld = _parse_ld_json_jobposting(html)
    base = _parse_detail_fields_from_ld(ld) if ld else _parse_detail_fields_fallback(html)

    if not base.get("description"):
        fb = _parse_detail_fields_fallback(html)
        if fb.get("description"):
            base["description"] = fb["description"]
        for key in ("salary_raw", "employment_type", "city", "state"):
            if base.get(key) is None and fb.get(key) is not None:
                base[key] = fb[key]

    return base


class Crawl4AIUSAJobsAdapter(SourceAdapter):
    """Concrete adapter for Crawl4AI — USAJobs federal portal."""

    def __init__(self, target_urls: list[str] | None = None) -> None:
        # Optional override for testing; default builds URL from RegionConfig.
        self._target_urls = target_urls or []

    @property
    def source_name(self) -> str:
        return "crawl4ai_usajobs"

    def _build_search_url(self, region: RegionConfig) -> str:
        """Build https://www.usajobs.gov/Search/Results?k=...&l=... from region."""
        if self._target_urls:
            return self._target_urls[0]
        parts: dict[str, str] = {}
        k = " ".join(x.strip() for x in region.keywords if x and x.strip())
        if k:
            parts["k"] = k
        loc = (region.query_location or "").strip()
        if loc:
            parts["l"] = loc
        if not parts:
            parts["k"] = "jobs"
        q = urlencode(parts)
        return f"{USAJOBS_SEARCH_BASE}?{q}"

    def _extract_job_cards(self, html: str) -> list[dict[str, Any]]:
        """Extract job links from listing HTML. {external_id, title, job_url}."""
        if not html:
            return []
        jobs: list[dict[str, Any]] = []
        seen: set[str] = set()

        for m in _JOB_URL_FULL_RE.finditer(html):
            job_id, slug = m.group(1), m.group(2) or ""
            if job_id in seen:
                continue
            seen.add(job_id)
            job_url = f"https://www.usajobs.gov/job/{job_id}/{slug}".rstrip("/")
            title = _title_from_slug(slug) or f"Job {job_id}"
            jobs.append({"external_id": job_id, "title": title, "job_url": job_url})

        for m in _JOB_URL_REL_RE.finditer(html):
            path, job_id = m.group(1), m.group(2)
            if job_id in seen:
                continue
            seen.add(job_id)
            job_url = _normalize_url(path, USAJOBS_BASE)
            segs = [p for p in path.split("/") if p]
            slug = segs[2] if len(segs) > 2 else ""
            title = _title_from_slug(slug) or f"Job {job_id}"
            jobs.append({"external_id": job_id, "title": title, "job_url": job_url})

        return jobs

    def _to_raw_job_record(
        self,
        card: dict[str, Any],
        region: RegionConfig,
        detail: dict[str, Any] | None,
        index: int,
    ) -> RawJobRecord:
        """Merge listing card with optional detail scrape into RawJobRecord."""
        external_id = _normalize_str(str(card.get("external_id", str(index))))
        title = _normalize_str(str(card.get("title", "Unknown")))
        job_url = _normalize_str(str(card.get("job_url", "")))

        description = ""
        salary_raw = None
        employment_type = None
        city = None
        state = None
        company = _normalize_str("U.S. Federal Government")

        if detail:
            if detail.get("title"):
                title = _normalize_str(str(detail["title"])) or title
            description = _normalize_str(str(detail.get("description") or ""))
            salary_raw = detail.get("salary_raw")
            if salary_raw is not None:
                salary_raw = _normalize_str(str(salary_raw)) or None
            employment_type = detail.get("employment_type")
            if employment_type is not None:
                employment_type = _normalize_str(str(employment_type)) or None
            city = detail.get("city")
            if city is not None:
                city = _normalize_str(str(city)) or None
            state = detail.get("state")
            if state is not None:
                state = _normalize_str(str(state)) or None
            if detail.get("company"):
                company = _normalize_str(str(detail["company"])) or company

        region_id = _normalize_str(region.region_id)
        raw_hash = hashlib.sha256(f"crawl4ai_usajobs|{external_id}|{title}|{job_url}".encode()).hexdigest()
        payload: dict[str, Any] = {
            "external_id": external_id,
            "title": title,
            "job_url": job_url,
        }
        if detail:
            payload["detail"] = dict(detail)

        return RawJobRecord(
            external_id=external_id,
            source="crawl4ai_usajobs",
            region_id=region_id,
            raw_payload_hash=raw_hash,
            title=title,
            company=company,
            description=description,
            city=city,
            state=state,
            country=None,
            is_remote=None,
            date_posted=None,
            date_ingested=datetime.utcnow(),
            salary_raw=salary_raw,
            salary_min=None,
            salary_max=None,
            salary_currency="USD" if salary_raw else None,
            salary_period=None,
            employment_type=employment_type,
            experience_level=None,
            job_url=job_url or None,
            source_url=USAJOBS_SEARCH_BASE,
            raw_payload=payload,
        )

    async def fetch(self, region: RegionConfig) -> list[RawJobRecord]:
        """Two-pass fetch: listing links, then concurrent detail pages (max 5)."""
        from crawl4ai import AsyncWebCrawler, BrowserConfig

        url = self._build_search_url(region)
        cfg = _spa_crawl_config()

        try:
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                result = await crawler.arun(url, config=cfg)

                if not result.success:
                    msg = getattr(result, "error_message", str(result)) or "unknown"
                    raise Crawl4AIUSAJobsAdapterError(f"Target unreachable: {msg}")

                html = getattr(result, "html", None) or getattr(result, "cleaned_html", None)
                if html is None:
                    raise Crawl4AIUSAJobsAdapterError("Crawl result missing html and cleaned_html")
                html = str(html) if html else ""

                if len(html) < _MIN_HTML_LEN:
                    raise Crawl4AIUSAJobsAdapterError(f"Page content too small ({len(html)} chars)")

                no_results = _NO_RESULTS_RE.search(html) is not None
                cards = self._extract_job_cards(html)

                if not cards and len(html) >= _MIN_HTML_LEN:
                    if no_results:
                        return []
                    raise Crawl4AIUSAJobsAdapterError("Large page with zero job links; possible parser breakage")

                sem = asyncio.Semaphore(5)

                async def _fetch_one_detail(job_url: str) -> dict[str, Any] | None:
                    async with sem:
                        try:
                            dr = await crawler.arun(job_url, config=cfg)
                        except Exception as e:
                            log.warning(
                                "usajobs_detail_fetch_failed",
                                job_url=job_url,
                                error=str(e),
                            )
                            return None
                        if not dr.success:
                            log.warning(
                                "usajobs_detail_crawl_unsuccessful",
                                job_url=job_url,
                                error=getattr(dr, "error_message", None) or "unknown",
                            )
                            return None
                        dhtml = getattr(dr, "html", None) or getattr(dr, "cleaned_html", None)
                        if dhtml is None:
                            log.warning(
                                "usajobs_detail_missing_html",
                                job_url=job_url,
                            )
                            return None
                        return _parse_detail_html(str(dhtml))

                detail_results = await asyncio.gather(*[_fetch_one_detail(str(c["job_url"])) for c in cards])

                records: list[RawJobRecord] = []
                for i, card in enumerate(cards):
                    detail = detail_results[i] if i < len(detail_results) else None
                    records.append(self._to_raw_job_record(card, region, detail, i))
                return records
        except Crawl4AIUSAJobsAdapterError:
            raise
        except Exception as e:
            raise Crawl4AIUSAJobsAdapterError(f"Crawl4AI init/fetch failed: {e}") from e

    async def health_check(self) -> dict:
        """Probe USAJobs search reachability with the same SPA crawl settings."""
        from crawl4ai import AsyncWebCrawler, BrowserConfig

        probe_url = (
            self._target_urls[0]
            if self._target_urls
            else f"{USAJOBS_SEARCH_BASE}?k=information%20technology&l=Washington%2C%20DC"
        )
        cfg = _spa_crawl_config()
        try:
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                result = await crawler.arun(probe_url, config=cfg)
            success = bool(getattr(result, "success", False))
            html = getattr(result, "html", None) or getattr(result, "cleaned_html", None)
            html_str = str(html) if html else ""
            ok = success and len(html_str) >= _MIN_HTML_LEN
            err_msg = None
            if not success:
                err_msg = getattr(result, "error_message", None) or "crawl failed"
            elif len(html_str) < _MIN_HTML_LEN:
                err_msg = f"HTML too small ({len(html_str)} chars)"
            return {
                "status": "ok" if ok else "error",
                "source": "crawl4ai_usajobs",
                "reachable": success,
                "error": err_msg,
            }
        except Exception as e:
            return {
                "status": "error",
                "source": "crawl4ai_usajobs",
                "reachable": False,
                "error": str(e),
            }
