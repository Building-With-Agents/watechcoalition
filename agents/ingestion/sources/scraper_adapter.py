"""
Scrape 5–10 job postings from listing page(s) using Crawl4AI.
Strategy: crawl listing (strict link extraction) → if no links, fall back to RSS → crawl each job URL.
Saves raw output to agents/data/staging/raw_scrape_sample.json.
Uses structlog, SCRAPING_TARGETS env var. No PII, no hardcoded credentials.
"""
import asyncio
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import structlog
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv
import httpx

# Load agents/.env
_agents_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_agents_root / ".env")

log = structlog.get_logger()

OUTPUT_PATH = _agents_root / "data" / "staging" / "raw_scrape_sample.json"
SOURCE_ID = "scraper"
MAX_POSTINGS = 10
MIN_POSTINGS = 5
MIN_RAW_TEXT_LENGTH = 200
MAX_JOB_LINK_CANDIDATES = 50

# RSS fallback when listing page yields no job links (JS-heavy pages)
PYTHON_JOBS_RSS_URL = "https://www.python.org/jobs/feed/rss/"

# Tokens that must appear at least once in raw_text for a posting to be valid (case-insensitive)
VALID_POSTING_TOKENS = ("apply", "responsibilities", "requirements", "job", "role", "position")

# Non-job path prefixes to exclude (Python Job Board)
EXCLUDED_PATH_PREFIXES = (
    "/",
    "/psf/",
    "/downloads/",
    "/doc/",
    "/community/",
    "/events/",
    "/blogs/",
    "/about/",
    "/accounts/",
    "/search/",
)

# www.python.org/jobs/<id>/ style (e.g. /jobs/8044/)
PYTHON_ORG_JOBS_PATTERN = re.compile(r"^/jobs/[^/]+/?$", re.I)

# Accept job links from either Python Job Board host
PYTHON_JOBBOARD_NETLOCS = ("www.python.org", "jobs.python.org")


def _is_excluded_path(path: str) -> bool:
    path_normalized = (path or "/").rstrip("/") or "/"
    if path_normalized == "/":
        return True
    for prefix in EXCLUDED_PATH_PREFIXES:
        p = prefix.rstrip("/")
        if path_normalized == p or path_normalized.startswith(p + "/"):
            return True
    return False


def _is_job_detail_url(url: str, listing_url: str) -> bool:
    """Return True only for known job detail patterns: jobs.python.org or www.python.org/jobs/<id>/."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    netloc = (parsed.netloc or "").lower()

    if _is_excluded_path(path):
        return False
    if netloc == "jobs.python.org":
        # jobs.python.org: path should look like a detail page (not root, not excluded)
        return len(path.strip("/").split("/")) >= 1 and path.strip("/") != ""
    if netloc == "www.python.org":
        # www.python.org/jobs/<id>/ style
        return bool(PYTHON_ORG_JOBS_PATTERN.match(path))
    return False


def extract_job_links(html: str, listing_url: str) -> list[str]:
    """Extract job detail links from listing page HTML. Site-aware: only Python Job Board job URLs."""
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")

    seen: set[str] = set()
    links: list[str] = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue
        full_url = urljoin(listing_url, href)
        parsed = urlparse(full_url)
        if (parsed.netloc or "").lower() not in PYTHON_JOBBOARD_NETLOCS:
            continue
        clean = parsed._replace(fragment="").geturl()
        if clean in seen:
            continue
        if not _is_job_detail_url(clean, listing_url):
            continue
        seen.add(clean)
        if clean.rstrip("/") == listing_url.rstrip("/"):
            continue
        links.append(clean)
        if len(links) >= MAX_JOB_LINK_CANDIDATES:
            break

    return links[:MAX_JOB_LINK_CANDIDATES]


async def scrape_job_detail(
    crawler: AsyncWebCrawler,
    job_url: str,
    listing_url: str,
) -> dict | None:
    """Crawl a job detail URL and return a posting dict."""
    try:
        result = await crawler.arun(url=job_url)
        if not result.success:
            log.warning("scrape_failed", url=job_url, success=False)
            return None
        scraped_at = datetime.now(timezone.utc).isoformat()
        md = result.markdown
        if md is None:
            raw_text = ""
        elif hasattr(md, "raw_markdown") and md.raw_markdown:
            raw_text = str(md.raw_markdown)
        else:
            raw_text = str(md) if md else ""
        raw_html = getattr(result, "html", None) or ""
        return {
            "source": SOURCE_ID,
            "listing_url": listing_url,
            "url": getattr(result, "url", None) or job_url,
            "scraped_at": scraped_at,
            "raw_text": raw_text,
            "raw_html": raw_html if raw_html else None,
        }
    except Exception as e:
        log.warning("scrape_error", url=job_url, error=str(e))
        return None


def _is_valid_posting(posting: dict) -> bool:
    """Valid iff url non-empty, raw_text >= MIN_RAW_TEXT_LENGTH, and contains at least one job-related token."""
    url = (posting.get("url") or "").strip()
    raw_text = posting.get("raw_text") or ""
    if not url or len(raw_text) < MIN_RAW_TEXT_LENGTH:
        return False
    text_lower = raw_text.lower()
    return any(t in text_lower for t in VALID_POSTING_TOKENS)


def _fetch_rss_job_links(rss_url: str, max_links: int = 10) -> list[str]:
    """Fetch RSS feed and return first max_links job detail URLs from <item><link>."""
    links: list[str] = []
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(rss_url)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
    except Exception as e:
        log.warning("rss_fetch_failed", url=rss_url, error=str(e))
        return []
    # RSS 2.0: <channel><item><link>...</link></item></channel>; namespaces possible
    for item in root.iter():
        tag = item.tag.split("}")[-1] if "}" in item.tag else item.tag
        if tag != "item":
            continue
        for child in item:
            ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if ctag != "link":
                continue
            url = (child.text or child.get("href") or "").strip()
            if url and url not in links:
                links.append(url)
                if len(links) >= max_links:
                    return links
            break
    return links[:max_links]


async def run_scrape() -> None:
    """Scrape listing page(s), extract job links, crawl each, validate, save JSON."""
    targets_raw = os.getenv("SCRAPING_TARGETS", "")
    if not targets_raw:
        log.error("scrape_config_missing", error="SCRAPING_TARGETS not set")
        raise SystemExit(1)

    listing_urls = [u.strip() for u in targets_raw.split(",") if u.strip()]
    if not listing_urls:
        log.error("scrape_config_empty", error="SCRAPING_TARGETS has no valid URLs")
        raise SystemExit(1)

    target_url = listing_urls[0]
    scraped_at = datetime.now(timezone.utc).isoformat()
    seen_job_urls: set[str] = set()
    raw_postings: list[dict] = []

    async with AsyncWebCrawler() as crawler:
        for listing_url in listing_urls:
            result = await crawler.arun(url=listing_url)
            html = getattr(result, "html", None) or ""
            log.info(
                "listing_crawl",
                url=listing_url,
                success=result.success,
                html_bytes=len(html),
            )
            if not result.success:
                log.warning("listing_crawl_failed", url=listing_url)
                continue

            job_links = extract_job_links(html, listing_url)
            log.info(
                "job_link_candidates",
                url=listing_url,
                candidate_count=len(job_links),
            )
            if not job_links:
                log.warning("fallback_to_rss", listing_url=listing_url)
                job_links = _fetch_rss_job_links(PYTHON_JOBS_RSS_URL, max_links=10)
                if not job_links:
                    log.warning("no_job_links_found", url=listing_url)
                    continue

            for job_url in job_links:
                valid_count = len([p for p in raw_postings if _is_valid_posting(p)])
                if valid_count >= MAX_POSTINGS:
                    break
                if job_url in seen_job_urls:
                    continue
                seen_job_urls.add(job_url)
                posting = await scrape_job_detail(crawler, job_url, listing_url)
                if posting:
                    raw_postings.append(posting)
                    valid_count = len([p for p in raw_postings if _is_valid_posting(p)])
                    if valid_count >= MAX_POSTINGS:
                        break
            valid_count = len([p for p in raw_postings if _is_valid_posting(p)])
            if valid_count >= MIN_POSTINGS:
                break

    valid_postings = [p for p in raw_postings if _is_valid_posting(p)]
    invalid_count = len(raw_postings) - len(valid_postings)
    log.info(
        "postings_validated",
        valid_count=len(valid_postings),
        invalid_count=invalid_count,
    )

    payload = {
        "source": SOURCE_ID,
        "target_url": target_url,
        "scraped_at": scraped_at,
        "postings": valid_postings,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    log.info("raw_scrape_result", url=target_url, record_count=len(valid_postings))


def main() -> None:
    """Entry point for python -m agents.ingestion.sources.scraper_adapter."""
    asyncio.run(run_scrape())


if __name__ == "__main__":
    main()
