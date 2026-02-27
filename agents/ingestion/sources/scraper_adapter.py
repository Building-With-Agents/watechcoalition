# agents/ingestion/sources/scraper_adapter.py
"""
Web scraping via Crawl4AI. Phase 1.

Scrapes job listing page(s) from SCRAPING_TARGETS, extracts 5–10 raw job-like
payloads with canonical fields for downstream (normalization, enrichment). Each
record includes: url, title, company, source_url, description; optionally
date_posted, location, salary_raw, employment_type. No DB, Prisma, or
SQLAlchemy. Can be run as a script to write results to
agents/data/staging/raw_scrape_sample.json.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import structlog
from dotenv import load_dotenv

log = structlog.get_logger()

# Canonical keys for each raw job posting (downstream: normalization, enrichment)
RAW_JOB_KEYS = (
    "url",
    "title",
    "company",
    "source_url",
    "description",
    "date_posted",
    "location",
    "salary_raw",
    "employment_type",
)

# Job-like path segments (case-insensitive) used to filter links
_JOB_PATH_PATTERN = re.compile(
    r"job|career|position|opening|vacancy|role|opportunit",
    re.IGNORECASE,
)
# Exclude policy/legal links (privacy, terms, etc.) from job results
_NON_JOB_PATH_PATTERN = re.compile(
    r"privacy|terms-of-use|terms_of_use|cookie-policy|cookies|legal|policy|disclaimer|gdpr|ccpa",
    re.IGNORECASE,
)
_MAX_JOBS = 10
_MAX_DESCRIPTION_LEN = 50_000
# Short description for each job (snippet length)
_MAX_SHORT_DESCRIPTION_CHARS = 500


def _repo_root() -> Path:
    """Return repo root (parent of agents/). Works from repo root or agents/."""
    return Path(__file__).resolve().parents[3]


# Load .env from repo root so SCRAPING_TARGETS is available when run as script
load_dotenv(_repo_root() / ".env")


def _staging_path() -> Path:
    """Path to raw_scrape_sample.json under agents/data/staging."""
    return _repo_root() / "agents" / "data" / "staging" / "raw_scrape_sample.json"


def _normalize_target_url(raw: str) -> str:
    """Ensure URL has http(s) scheme so Crawl4AI accepts it."""
    s = raw.strip()
    if not s:
        return s
    if not s.startswith(("http://", "https://", "file://", "raw:")):
        return "https://" + s
    return s


def _to_canonical_raw_record(partial: dict, source_url: str) -> dict:
    """Ensure record has all RAW_JOB_KEYS; set missing optional fields to None."""
    out = {k: partial.get(k) for k in RAW_JOB_KEYS if k in partial}
    for k in RAW_JOB_KEYS:
        if k not in out:
            out[k] = None if k != "source_url" else source_url
    out["source_url"] = source_url
    out["url"] = partial.get("url") or out["url"]
    out["title"] = partial.get("title") or out["title"] or ""
    return out


def _strip_html(html: str) -> str:
    """Remove HTML tags and normalize whitespace for regex extraction."""
    if not html:
        return ""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_job_detail(html: str) -> dict:
    """
    Heuristic extraction of company, description, date_posted, location,
    salary_raw, employment_type from job detail page HTML. No PII.
    """
    text = _strip_html(html)
    if len(text) > _MAX_DESCRIPTION_LEN:
        text = text[:_MAX_DESCRIPTION_LEN]
    out: dict[str, str | None] = {
        "company": None,
        "description": None,
        "date_posted": None,
        "location": None,
        "salary_raw": None,
        "employment_type": None,
    }
    if not text:
        return out
    # Short description: first N chars, optionally cut at last sentence end
    raw = text.strip()
    if len(raw) > _MAX_SHORT_DESCRIPTION_CHARS:
        snippet = raw[:_MAX_SHORT_DESCRIPTION_CHARS]
        last_period = snippet.rfind(". ")
        if last_period > _MAX_SHORT_DESCRIPTION_CHARS // 2:
            snippet = snippet[: last_period + 1]
        out["description"] = snippet.strip()
    else:
        out["description"] = raw
    # Company: common labels
    for pat in (
        r"(?:company|organization|employer|hiring company)\s*[:\-]\s*([^\n|]+)",
        r"(?:at|@)\s+([A-Za-z0-9\s&.,\-]+?)(?:\s*[|\-]\s|\s+-\s+|$)",
        r"<meta[^>]+property=[\"']og:site_name[\"'][^>]+content=[\"']([^\"']+)[\"']",
    ):
        m = re.search(pat, html if "meta" in pat else text, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            if len(cand) < 2 or len(cand) > 200:
                continue
            out["company"] = cand[:200]
            break
    # Date posted
    for pat in (
        r"(?:posted|date posted|published)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})",
        r"(?:posted|date)\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            out["date_posted"] = m.group(1).strip()[:50]
            break
    # Location
    for pat in (
        r"(?:location|place|where)\s*[:\-]\s*([^\n|]+?)(?:\n|$|\|)",
        r"(remote|anywhere|distributed|worldwide)",
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            out["location"] = m.group(1).strip()[:255]
            break
    # Salary
    for pat in (
        r"(?:salary|compensation|pay)\s*[:\-]\s*([^\n]+?)(?:\n|$)",
        r"(\$[\d,]+(?:\s*-\s*\$?[\d,]+)?(?:\s*/\s*(?:hour|yr|year|annum))?)",
        r"([€£]\s*[\d,]+(?:\s*[-–]\s*[€£]?\s*[\d,]+)?)",
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            out["salary_raw"] = m.group(1).strip()[:255]
            break
    # Employment type
    for pat in (
        r"(?:employment type|job type|type)\s*[:\-]\s*([^\n|]+)",
        r"\b(full[- ]?time|part[- ]?time|contract|temporary|internship|freelance)\b",
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            out["employment_type"] = m.group(1).strip()[:100]
            break
    return out


class _LinkExtractor(HTMLParser):
    """Extract (href, text) from <a> tags. No PII logged or stored."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = None
        for k, v in attrs:
            if k == "href" and v:
                href = v.strip()
                break
        if href and not href.startswith(("#", "javascript:")):
            self.links.append((href, ""))

    def handle_data(self, data: str) -> None:
        if self.links and data:
            href, _ = self.links[-1]
            self.links[-1] = (href, (self.links[-1][1] + data).strip()[:500])


def _extract_job_links(html: str, base_url: str) -> list[dict]:
    """Parse HTML and return up to _MAX_JOBS job-like link payloads."""
    parser = _LinkExtractor()
    try:
        parser.feed(html)
    except Exception:
        return []
    seen: set[str] = set()
    out: list[dict] = []
    for href, text in parser.links:
        if len(out) >= _MAX_JOBS:
            break
        full_url = urljoin(base_url, href)
        path = urlparse(full_url).path or ""
        if not _JOB_PATH_PATTERN.search(path) and not _JOB_PATH_PATTERN.search(href):
            continue
        if _NON_JOB_PATH_PATTERN.search(path) or _NON_JOB_PATH_PATTERN.search(href):
            continue
        link_text_lower = (text or "").lower()
        if _NON_JOB_PATH_PATTERN.search(link_text_lower):
            continue
        norm = full_url.rstrip("/")
        if norm in seen:
            continue
        seen.add(norm)
        out.append({
            "url": full_url,
            "title": (text or path or full_url)[:500],
            "source_url": base_url,
        })
    return out


def _crawl_config():
    """Config to dismiss cookie/consent overlays so we capture job content, not the popup."""
    from crawl4ai import CrawlerRunConfig

    return CrawlerRunConfig(
        remove_overlay_elements=True,
        delay_before_return_html=0.8,
    )


async def _crawl(listing_url: str) -> list[dict]:
    """Crawl listing URL, then each job link, and return canonical raw job payloads."""
    from crawl4ai import AsyncWebCrawler

    url = _normalize_target_url(listing_url)
    config = _crawl_config()
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        if not getattr(result, "success", True):
            log.warning("crawl_failed", url=url, error=getattr(result, "error_message", "unknown"))
            return []
        html = getattr(result, "html", None)
        if not html and hasattr(result, "markdown"):
            md = result.markdown
            html = getattr(md, "raw_markdown", None) if md is not None else None
        if not html:
            log.warning("crawl_no_content", url=url)
            return []
        links = _extract_job_links(html, url)
        if not links:
            links = [{"url": url, "title": "", "source_url": url}]
        records: list[dict] = []
        for partial in links[: _MAX_JOBS]:
            rec = _to_canonical_raw_record(partial, url)
            job_url = rec.get("url")
            if job_url and job_url != url:
                job_url = _normalize_target_url(job_url)
                try:
                    job_result = await crawler.arun(url=job_url, config=config)
                    if getattr(job_result, "success", True):
                        job_html = getattr(job_result, "html", None)
                        if not job_html and hasattr(job_result, "markdown"):
                            job_md = job_result.markdown
                            job_html = getattr(job_md, "raw_markdown", None) if job_md else None
                        if job_html:
                            detail = _parse_job_detail(job_html)
                            for k, v in detail.items():
                                if v is not None and v != "":
                                    rec[k] = v
                except Exception:
                    pass
            rec["url"] = _normalize_target_url(rec.get("url") or "")
            records.append(rec)
    return records


def _target_urls(url: str | None) -> list[str]:
    """Return list of URLs: single url if provided, else parse SCRAPING_TARGETS (comma-separated)."""
    if url and url.strip():
        return [_normalize_target_url(url.strip())]
    raw = os.getenv("SCRAPING_TARGETS", "").strip()
    if not raw:
        return []
    return [_normalize_target_url(s.strip()) for s in raw.split(",") if s.strip()]


async def _crawl_all(urls: list[str]) -> list[dict]:
    """Crawl each URL and return combined list of canonical raw job records."""
    all_records: list[dict] = []
    for u in urls:
        records = await _crawl(u)
        all_records.extend(records)
        log.info("raw_scrape_result", url=u, record_count=len(records))
    return all_records


def scrape_jobs(url: str | None = None) -> list[dict] | None:
    """
    Scrape job postings from the given URL or from all SCRAPING_TARGETS.

    Reads SCRAPING_TARGETS (comma-separated list); if url is provided uses that
    single URL. Scans every target URL and returns combined list of canonical
    raw job dicts (url, title, company, source_url, description; optionally
    date_posted, location, salary_raw, employment_type). None if no target. No PII.
    """
    urls = _target_urls(url)
    if not urls:
        log.warning("scraper_no_target", reason="SCRAPING_TARGETS not set or empty")
        return None
    records = asyncio.run(_crawl_all(urls))
    log.info("raw_scrape_complete", url_count=len(urls), total_record_count=len(records))
    return records


def save_raw_scrape(records: list[dict], path: Path | None = None) -> Path:
    """Write list of raw payloads to JSON file. Creates parent dirs if needed."""
    out = path or _staging_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    return out


if __name__ == "__main__":
    records = scrape_jobs()
    if records is not None:
        out_path = save_raw_scrape(records)
        log.info("raw_scrape_saved", path=str(out_path), record_count=len(records))
