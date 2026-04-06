"""Crawl4AI source adapter — Indeed job search (www.indeed.com).

Contract: implements SourceAdapter. Output is list[RawJobRecord].
Target: https://www.indeed.com/jobs (q, l from RegionConfig).

Indeed often serves Cloudflare challenges to automated browsers. Listing and detail
logic treat blocks as soft failures: log a warning and return partial or empty
results — fetch() does not raise for blocked or failed crawls.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import structlog

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.base_adapter import SourceAdapter

log = structlog.get_logger()

# Minimum HTML length for a normal-looking SERP (below this + no CF markers may
# still be blocked; see _is_crawl_blocked).
_MIN_HTML_LEN = 500

INDEED_BASE = "https://www.indeed.com"
INDEED_JOBS_URL = f"{INDEED_BASE}/jobs"

# Indeed job keys (jk) are typically 16 hex chars in URLs and data-jk attributes.
_JK_RE = re.compile(
    r'(?:data-jk="|\b[?&]jk=)([a-f0-9]{16})"',
    re.I,
)

_NO_RESULTS_RE = re.compile(
    r"\b(no\s+jobs?\s+match|no\s+job\s+results|did\s+not\s+match\s+any\s+jobs)\b",
    re.I,
)

_CF_MARKERS: tuple[str, ...] = (
    "cf-ray",
    "cloudflare",
    "just a moment",
    "challenge-platform",
    "cf-browser-verification",
    "attention required",
    "sorry, you have been blocked",
    "checking your browser",
    "__cf_bm",
    "enable javascript and cookies",
    "ddos protection by cloudflare",
)

_EMPLOYMENT_FALLBACK_RE = re.compile(
    r"\b(full[- ]time|part[- ]time|contract|temporary|internship|commission)\b",
    re.I,
)

_SALARY_FALLBACK_RE = re.compile(
    r"\$[\d,]+(?:\.\d{2})?(?:\s*-\s*\$?[\d,]+(?:\.\d{2})?)?"
    r"(?:\s*/\s*(?:year|yr|hour|hr|annually|per\s+hour))?",
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


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags; collapse whitespace (no external deps)."""
    if not html:
        return ""
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return _normalize_str(text)


def _indeed_crawl_config() -> Any:
    """Match crawl4ai_adapter: BYPASS cache only (no extra SPA wait)."""
    from crawl4ai import CacheMode, CrawlerRunConfig

    return CrawlerRunConfig(cache_mode=CacheMode.BYPASS)


def _html_has_cloudflare_signals(html: str) -> bool:
    hl = (html or "").lower()
    return any(m in hl for m in _CF_MARKERS)


def _is_crawl_blocked(html: str, success: bool) -> bool:
    """True when listing/detail response looks blocked or unusable."""
    if not success:
        return True
    h = html or ""
    if not h.strip():
        return True
    if len(h.strip()) < 100:
        return True
    return _html_has_cloudflare_signals(h)


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
    """Extract detail fields from a job posting HTML page."""
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


def _title_near_jk(html: str, jk: str) -> str:
    """Best-effort job title from listing HTML near a jk marker."""
    needle = f'data-jk="{jk}"'
    i = html.find(needle)
    if i < 0:
        needle2 = f"jk={jk}"
        i = html.find(needle2)
    if i < 0:
        return ""
    chunk = html[i : i + 4000]
    m = re.search(
        r'class="[^"]*jobTitle[^"]*"[^>]*>(?:<span[^>]*>)?([^<]+)',
        chunk,
        re.I,
    )
    if m:
        return _normalize_str(m.group(1))
    m2 = re.search(
        r'data-testid="job-title"[^>]*>([^<]+)',
        chunk,
        re.I,
    )
    return _normalize_str(m2.group(1)) if m2 else ""


class Crawl4AIIndeedAdapter(SourceAdapter):
    """Concrete adapter for Crawl4AI — Indeed job search."""

    def __init__(self, target_urls: list[str] | None = None) -> None:
        self._target_urls = target_urls or []

    @property
    def source_name(self) -> str:
        return "crawl4ai_indeed"

    def _build_search_url(self, region: RegionConfig) -> str:
        """Build https://www.indeed.com/jobs?q=...&l=... from region."""
        if self._target_urls:
            return self._target_urls[0]
        parts: dict[str, str] = {}
        q = " ".join(x.strip() for x in region.keywords if x and x.strip())
        if q:
            parts["q"] = q
        loc = (region.query_location or "").strip()
        if loc:
            parts["l"] = loc
        if not parts:
            parts["q"] = "jobs"
        return f"{INDEED_JOBS_URL}?{urlencode(parts)}"

    def _extract_job_cards(self, html: str) -> list[dict[str, Any]]:
        """Extract job keys from listing HTML. {external_id, title, job_url}."""
        if not html:
            return []
        jobs: list[dict[str, Any]] = []
        seen: set[str] = set()
        for m in _JK_RE.finditer(html):
            jk = m.group(1).lower()
            if jk in seen:
                continue
            seen.add(jk)
            job_url = f"{INDEED_BASE}/viewjob?jk={jk}"
            title = _title_near_jk(html, jk) or f"Job {jk[:8]}"
            jobs.append({"external_id": jk, "title": title, "job_url": job_url})
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
        company = _normalize_str("Unknown")

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
        raw_hash = hashlib.sha256(f"crawl4ai_indeed|{external_id}|{title}|{job_url}".encode()).hexdigest()
        payload: dict[str, Any] = {
            "external_id": external_id,
            "title": title,
            "job_url": job_url,
        }
        if detail:
            payload["detail"] = dict(detail)

        return RawJobRecord(
            external_id=external_id,
            source="crawl4ai_indeed",
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
            source_url=INDEED_JOBS_URL,
            raw_payload=payload,
        )

    async def fetch(self, region: RegionConfig) -> list[RawJobRecord]:
        """Two-pass fetch; Cloudflare blocks yield [] with warnings — no raises."""
        try:
            return await self._fetch_impl(region)
        except Exception as e:
            log.warning("indeed_fetch_exception", error=str(e))
            return []

    async def _fetch_impl(self, region: RegionConfig) -> list[RawJobRecord]:
        from crawl4ai import AsyncWebCrawler, BrowserConfig

        url = self._build_search_url(region)
        cfg = _indeed_crawl_config()

        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            result = await crawler.arun(url, config=cfg)

            html = getattr(result, "html", None) or getattr(result, "cleaned_html", None)
            html_str = str(html) if html is not None else ""

            if _is_crawl_blocked(html_str, bool(getattr(result, "success", False))):
                log.warning(
                    "indeed_listing_blocked_or_empty",
                    search_url=url,
                    success=getattr(result, "success", False),
                    html_len=len(html_str),
                    cf_signals=_html_has_cloudflare_signals(html_str),
                )
                return []

            if len(html_str) < _MIN_HTML_LEN:
                log.warning(
                    "indeed_listing_html_too_small",
                    search_url=url,
                    html_len=len(html_str),
                )
                return []

            no_results = _NO_RESULTS_RE.search(html_str) is not None
            cards = self._extract_job_cards(html_str)

            if not cards:
                if no_results:
                    return []
                log.warning(
                    "indeed_no_job_cards_extracted",
                    search_url=url,
                    html_len=len(html_str),
                )
                return []

            sem = asyncio.Semaphore(5)

            async def _fetch_one_detail(job_url: str) -> dict[str, Any] | None:
                async with sem:
                    try:
                        dr = await crawler.arun(job_url, config=cfg)
                    except Exception as e:
                        log.warning(
                            "indeed_detail_fetch_failed",
                            job_url=job_url,
                            error=str(e),
                        )
                        return None
                    dhtml = getattr(dr, "html", None) or getattr(dr, "cleaned_html", None)
                    dhtml_str = str(dhtml) if dhtml is not None else ""
                    if _is_crawl_blocked(dhtml_str, bool(getattr(dr, "success", False))):
                        log.warning(
                            "indeed_detail_blocked_or_empty",
                            job_url=job_url,
                            success=getattr(dr, "success", False),
                            html_len=len(dhtml_str),
                        )
                        return None
                    return _parse_detail_html(dhtml_str)

            detail_results = await asyncio.gather(*[_fetch_one_detail(str(c["job_url"])) for c in cards])

            records: list[RawJobRecord] = []
            for i, card in enumerate(cards):
                detail = detail_results[i] if i < len(detail_results) else None
                records.append(self._to_raw_job_record(card, region, detail, i))
            return records

    async def health_check(self) -> dict:
        """Probe Indeed jobs listing; blocked HTML is reported as error, not raised."""
        from crawl4ai import AsyncWebCrawler, BrowserConfig

        probe_url = self._target_urls[0] if self._target_urls else f"{INDEED_JOBS_URL}?q=software%20engineer&l=Remote"
        cfg = _indeed_crawl_config()
        try:
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                result = await crawler.arun(probe_url, config=cfg)
            success = bool(getattr(result, "success", False))
            html = getattr(result, "html", None) or getattr(result, "cleaned_html", None)
            html_str = str(html) if html else ""
            blocked = _is_crawl_blocked(html_str, success)
            ok = success and not blocked and len(html_str.strip()) >= _MIN_HTML_LEN
            err_msg = None
            if blocked:
                err_msg = "blocked_or_empty_response"
            elif not success:
                err_msg = getattr(result, "error_message", None) or "crawl failed"
            elif len(html_str.strip()) < _MIN_HTML_LEN:
                err_msg = f"HTML too small ({len(html_str)} chars)"
            return {
                "status": "ok" if ok else "error",
                "source": "crawl4ai_indeed",
                "reachable": success and not blocked,
                "error": err_msg,
            }
        except Exception as e:
            return {
                "status": "error",
                "source": "crawl4ai_indeed",
                "reachable": False,
                "error": str(e),
            }
