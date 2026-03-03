"""Scraper adapter (Crawl4AI) for job ingestion.

Scrapes 5-10 job-like sections from a target URL, logs with structlog,
and saves raw output to agents/data/staging/raw_scrape_sample.json.
- We Work Remotely / Remote.co: two-phase — scrape list page for job links, then scrape each
  job detail page (one record per page). Each list-page "card" corresponds to one job link.
- Other sites: single-page scrape; parses page into job "cards" (one entry per card) by
  detecting job-detail links and splitting HTML so each card is one posting.
Job content is truncated at apply/save phrases (e.g. "Apply now", "Save job") when present
so the next job or unrelated content is not included.
Each record includes: source identifier, scraped URL, timestamp, raw text body (optional title when derivable).
Configuration is from environment variables only; no hardcoded URLs or credentials.
No PII in logs.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx
import structlog
from crawl4ai import AsyncWebCrawler

log = structlog.get_logger()

# Default output path relative to agents/ directory
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = AGENTS_DIR / "data" / "staging"
RAW_SCRAPE_OUTPUT = STAGING_DIR / "raw_scrape_sample.json"

# Target count of job records to extract per scrape
MIN_JOBS = 5
MAX_JOBS = 10

# Keywords that indicate a real job posting (employment type or pay). Case-insensitive.
_EMPLOYMENT_TYPE_PATTERNS = re.compile(
    r"\b(?:full[- ]?time|part[- ]?time|permanent|internship|contract|temporary|temp|seasonal|volunteer|remote|hybrid)\b",
    re.IGNORECASE,
)
_PAY_PATTERNS = re.compile(
    r"\b(?:salary|compensation|pay|wage|hourly|annual|per year|per hour|per month|USD|\$|€|stipend)\b",
    re.IGNORECASE,
)


def _looks_like_job_posting(text: str) -> bool:
    """True if text contains employment-type or pay/salary keywords (excludes main page, nav, etc.)."""
    if not text or len(text.strip()) < 30:
        return False
    t = text.strip()
    return bool(_EMPLOYMENT_TYPE_PATTERNS.search(t) or _PAY_PATTERNS.search(t))


# Stop phrases: truncate job content at first occurrence so we don't include the next job or footer.
_APPLY_STOP_PHRASES = (
    "Apply now",
    "Save job",
    "Apply for this job",
    "Submit application",
    "Apply for job",
)


def _truncate_at_apply_section(text: str) -> str:
    """Return text up to and including the first apply/save phrase (case-insensitive), trimmed.
    If none found, return the original text. Used to avoid including the next job or unrelated content.
    """
    if not text or not text.strip():
        return text
    text_lower = text.lower()
    best_start: int | None = None
    best_end: int | None = None
    for phrase in _APPLY_STOP_PHRASES:
        idx = text_lower.find(phrase.lower())
        if idx != -1:
            end = idx + len(phrase)
            if best_start is None or idx < best_start:
                best_start = idx
                best_end = end
    if best_end is not None:
        return text[:best_end].strip()
    return text


# Nav/chrome: drop lines that are only image+link or known nav links (same-site).
_NAV_LINK_LABELS = frozenset(
    s.lower()
    for s in (
        "Find Jobs",
        "Top 100 Remote Companies",
        "Top Trending Remote Jobs",
        "Search by Job Category",
        "Sign in",
        "New!",
    )
)
_NAV_PATH_SUBSTRINGS = ("/account/", "/top-remote-companies", "/top-trending")
# Markdown line that is only an image+link: [![](...)](...)
_RE_IMAGE_LINK_ONLY = re.compile(r"^\s*\[!\[.*?\]\s*\(\s*[^)]*\s*\)\]\s*\(\s*[^)]*\s*\)\s*$")
# List item that is only a link: * [Label](url) or - [Label](url)
_RE_LIST_LINK = re.compile(r"^\s*[-*]\s*\[([^\]]*)\]\s*\(\s*([^)]+)\s*\)\s*$")


def _strip_nav_and_chrome(markdown: str, base_url: str = "") -> str:
    """Remove nav/logo/sidebar lines so the main job body remains. Keeps headings, paragraphs, lists that describe the role."""
    if not markdown or not markdown.strip():
        return markdown
    kept: list[str] = []
    for line in markdown.splitlines():
        s = line.strip()
        if not s:
            kept.append(line)
            continue
        # Drop lines that are only markdown image+link (e.g. logo)
        if _RE_IMAGE_LINK_ONLY.match(s):
            continue
        # Drop list items that are only a link to known nav
        m = _RE_LIST_LINK.match(s)
        if m:
            label, url = m.group(1).strip(), m.group(2).strip().lower()
            if label.lower() in _NAV_LINK_LABELS:
                continue
            if any(nav in url for nav in _NAV_PATH_SUBSTRINGS):
                continue
        kept.append(line)
    return "\n".join(kept)


def _get_target_url() -> str | None:
    """Read first scraping target from env. No hardcoded URLs."""
    targets = os.getenv("SCRAPING_TARGETS", "").strip()
    if not targets:
        return None
    return targets.split(",")[0].strip()


def _check_url_reachable(url: str, timeout_seconds: float = 10.0) -> bool:
    """Return True if the URL responds with a successful HTTP status. Failsafe before scrape.
    Tries GET if HEAD returns 403/405 or other non-2xx (some sites block or mishandle HEAD).
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout_seconds) as client:
            resp = client.head(url)
            if resp.status_code not in range(200, 400):
                resp = client.get(url)
            return 200 <= resp.status_code < 400
    except Exception as e:
        log.warning("url_unreachable", url=url, error=str(e))
        return False


# We Work Remotely: job detail path is /remote-jobs/{company}-{title}
_WWR_BASE = "https://weworkremotely.com"
_WWR_JOB_PATH_RE = re.compile(r"https?://(?:www\.)?weworkremotely\.com/remote-jobs/(?!search)[^/?#]+", re.IGNORECASE)
_WWR_JOB_PATH_RE_REL = re.compile(r"^/remote-jobs/(?!search)[^/?#]+", re.IGNORECASE)

# Remote.co: job detail path is /job-details/{id}
_REMOTECO_BASE = "https://remote.co"
_REMOTECO_JOB_PATH_RE = re.compile(r"https?://(?:www\.)?remote\.co/job-details/[^/?#]+", re.IGNORECASE)
_REMOTECO_JOB_PATH_RE_REL = re.compile(r"^/job-details/[^/?#]+", re.IGNORECASE)

# Generic: match href to job-detail paths (remote-jobs, job-details, /job/123) for card splitting
_JOB_LINK_HREF_RE = re.compile(
    r'href\s*=\s*["\']([^"\']*(?:/remote-jobs/|/job-details/|/job/\d+)[^"\']*)["\']',
    re.IGNORECASE,
)
# Block-level tags that often wrap a single job card (start tag)
_CARD_BLOCK_START_RE = re.compile(r"<(?:div|li|article|section)\s", re.IGNORECASE)
# Replace block boundaries and <br> with newline before stripping tags (preserve readability)
_BLOCK_END_AND_BR_RE = re.compile(
    r"</(?:div|li|p|h[1-6]|section|article)\s*>|<br\s*/?>",
    re.IGNORECASE,
)


def _title_from_markdown(markdown: str, max_length: int = 150) -> str:
    """Derive a short title from job detail markdown: first heading or first non-empty line."""
    if not markdown or not markdown.strip():
        return ""
    lines = [ln.strip() for ln in markdown.strip().splitlines() if ln.strip()]
    for line in lines:
        # Markdown heading
        if line.startswith("#"):
            title = re.sub(r"^#+\s*", "", line).strip()
            if title and len(title) <= max_length:
                return title
        if line and len(line) <= max_length and not line.startswith(("*", "-", "|")):
            return line
    return ""


def _title_from_url(job_url: str) -> str:
    """Derive a title from job URL slug (last path segment, hyphens to spaces)."""
    if not job_url:
        return ""
    path = urlparse(job_url).path.strip("/")
    if not path:
        return ""
    segment = path.split("/")[-1] or path
    return segment.replace("-", " ").strip() or ""


def _split_html_into_job_cards(html: str, page_url: str, max_cards: int = MAX_JOBS) -> list[dict]:
    """
    Split list-page HTML into one entry per job card by finding job-detail links
    and treating the content around each link as one card. Returns list of
    {"url": job_page_url, "raw_text": card_text}; url is the job link, raw_text
    is the card segment with tags stripped.
    """
    if not (html and html.strip()):
        return []
    parsed = urlparse(page_url)
    base = f"{parsed.scheme or 'https'}://{parsed.netloc or ''}"
    seen_urls: set[str] = set()
    cards: list[dict] = []

    # Find all job-link hrefs and their start positions
    matches = list(_JOB_LINK_HREF_RE.finditer(html))
    if not matches:
        return []

    for i, m in enumerate(matches):
        if len(cards) >= max_cards:
            break
        href = (m.group(1) or "").strip().split("?")[0].rstrip("/")
        if not href or href in seen_urls:
            continue
        try:
            full_url = href if href.startswith("http") else urljoin(base, href)
        except Exception:
            full_url = href
        seen_urls.add(full_url)

        # Card segment: from this link's start to the next link's start (or end)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        # Extend start to previous block boundary so we include card wrapper (e.g. div/li/article)
        block_matches = list(_CARD_BLOCK_START_RE.finditer(html[:start]))
        if block_matches:
            last_block = block_matches[-1]
            prev_start = last_block.start()
            if start - prev_start < 5000:
                start = prev_start
        segment = html[start:end]
        # Preserve line breaks: replace block end tags and <br> with newline before stripping
        segment = _BLOCK_END_AND_BR_RE.sub("\n", segment)
        # Strip all remaining tags
        text = re.sub(r"<[^>]+>", " ", segment)
        # Collapse spaces/tabs within lines, then collapse multiple newlines to at most 2
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        text = text.strip()
        if len(text) < 15:
            continue
        text = _strip_nav_and_chrome(text, full_url)
        if not _looks_like_job_posting(text):
            continue
        text = _truncate_at_apply_section(text)
        title = _title_from_url(full_url) or _title_from_markdown(text)
        cards.append({"url": full_url, "raw_text": text, "title": title or ""})
    return cards


def _extract_job_urls_weworkremotely(result) -> list[str]:
    """Extract job detail URLs from We Work Remotely list page (result.links, markdown, or html)."""
    seen: set[str] = set()
    out: list[str] = []

    def normalize(href: str) -> str | None:
        href = (href or "").strip().split("?")[0].rstrip("/")
        if _WWR_JOB_PATH_RE.match(href):
            return href
        if _WWR_JOB_PATH_RE_REL.match(href):
            return f"{_WWR_BASE}{href}" if href.startswith("/") else f"{_WWR_BASE}/{href}"
        return None

    links_obj = getattr(result, "links", None) or {}
    internal = links_obj.get("internal", []) if isinstance(links_obj, dict) else []
    for item in internal:
        if isinstance(item, dict):
            href = (item.get("href") or "").strip()
        elif isinstance(item, str):
            href = item.strip()
        else:
            continue
        u = normalize(href)
        if u and u not in seen:
            seen.add(u)
            out.append(u)
            if len(out) >= MAX_JOBS:
                return out
    if not out:
        for text in [getattr(getattr(result, "markdown", None), "raw_markdown", None) or "",
                     getattr(result, "html", None) or "",
                     getattr(result, "cleaned_html", None) or ""]:
            if not isinstance(text, str):
                continue
            for m in _WWR_JOB_PATH_RE.finditer(text):
                u = m.group(0).split("?")[0].rstrip("/")
                if u not in seen:
                    seen.add(u)
                    out.append(u)
                    if len(out) >= MAX_JOBS:
                        return out
            for m in _WWR_JOB_PATH_RE_REL.finditer(text):
                path = m.group(0).split("?")[0].rstrip("/")
                u = f"{_WWR_BASE}{path}" if path.startswith("/") else f"{_WWR_BASE}/{path}"
                if u not in seen:
                    seen.add(u)
                    out.append(u)
                    if len(out) >= MAX_JOBS:
                        return out
    return out


def _extract_job_urls_remoteco(result) -> list[str]:
    """Extract job detail URLs from Remote.co list page (result.links, markdown, or html)."""
    seen: set[str] = set()
    out: list[str] = []

    def normalize(href: str) -> str | None:
        href = (href or "").strip().split("?")[0].rstrip("/")
        if _REMOTECO_JOB_PATH_RE.match(href):
            return href
        if _REMOTECO_JOB_PATH_RE_REL.match(href):
            return f"{_REMOTECO_BASE}{href}" if href.startswith("/") else f"{_REMOTECO_BASE}/{href}"
        return None

    links_obj = getattr(result, "links", None) or {}
    internal = links_obj.get("internal", []) if isinstance(links_obj, dict) else []
    for item in internal:
        if isinstance(item, dict):
            href = (item.get("href") or "").strip()
        elif isinstance(item, str):
            href = item.strip()
        else:
            continue
        u = normalize(href)
        if u and u not in seen:
            seen.add(u)
            out.append(u)
            if len(out) >= MAX_JOBS:
                return out
    if not out:
        for text in [getattr(getattr(result, "markdown", None), "raw_markdown", None) or "",
                     getattr(result, "html", None) or "",
                     getattr(result, "cleaned_html", None) or ""]:
            if not isinstance(text, str):
                continue
            for m in _REMOTECO_JOB_PATH_RE.finditer(text):
                u = m.group(0).split("?")[0].rstrip("/")
                if u not in seen:
                    seen.add(u)
                    out.append(u)
                    if len(out) >= MAX_JOBS:
                        return out
            for m in _REMOTECO_JOB_PATH_RE_REL.finditer(text):
                path = m.group(0).split("?")[0].rstrip("/")
                u = f"{_REMOTECO_BASE}{path}" if path.startswith("/") else f"{_REMOTECO_BASE}/{path}"
                if u not in seen:
                    seen.add(u)
                    out.append(u)
                    if len(out) >= MAX_JOBS:
                        return out
    return out


async def _scrape_one_job_page(crawler, job_url: str) -> str:
    """Scrape one job announcement URL; return markdown or empty string on failure."""
    result = await crawler.arun(url=job_url)
    if not getattr(result, "success", True):
        return ""
    raw = getattr(result, "markdown", None)
    if hasattr(raw, "raw_markdown"):
        markdown = raw.raw_markdown or ""
    elif hasattr(raw, "fit_markdown") and raw.fit_markdown:
        markdown = raw.fit_markdown
    elif isinstance(raw, str):
        markdown = raw
    else:
        markdown = ""
    markdown = _strip_nav_and_chrome(markdown, job_url)
    markdown = _truncate_at_apply_section(markdown)
    return markdown


def _chunk_markdown_into_jobs(markdown: str, min_n: int = MIN_JOBS, max_n: int = MAX_JOBS) -> list[str]:
    """Split markdown into content chunks; caller filters to job postings only."""
    if not (markdown or markdown.strip()):
        return []

    # Split by markdown headers (## or ###) or by double newline to get sections
    sections = re.split(r"\n\s*#{2,3}\s+", markdown.strip())
    # Also split any single huge block by double newline
    expanded: list[str] = []
    for s in sections:
        s = s.strip()
        if not s:
            continue
        if "\n\n" in s and len(s) > 800:
            expanded.extend(block.strip() for block in s.split("\n\n") if block.strip())
        else:
            expanded.append(s)

    # Dedupe while preserving order, then cap
    seen: set[str] = set()
    unique: list[str] = []
    for s in expanded:
        if s in seen or len(s) < 20:
            continue
        seen.add(s)
        unique.append(s)
        if len(unique) >= max_n:
            break

    # If we have too few, split the first/longest section by paragraphs to reach min_n
    while len(unique) < min_n and unique:
        longest = max(unique, key=len)
        if len(longest) < 100:
            break
        idx = unique.index(longest)
        half = len(longest) // 2
        # Split at nearest newline
        split_at = longest.rfind("\n", 0, half + 1)
        if split_at <= 0:
            split_at = half
        first, second = longest[:split_at].strip(), longest[split_at:].strip()
        unique.pop(idx)
        if first:
            unique.insert(idx, first)
        if second:
            unique.insert(idx + 1, second)
        if len(unique) >= max_n:
            break

    return unique[:max_n]


async def scrape_url(url: str) -> list[dict]:
    """
    Scrape a single URL with Crawl4AI and return 5-10 job-like content records.
    Tries to split the page into one entry per job "card" (by detecting job-detail links
    in HTML). If that yields no cards, falls back to chunking markdown by headers/sections.
    Returns list of dicts with keys: index, source, url, raw_text (scraped_at added in run_scrape).
    """
    jobs: list[dict] = []
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        if not getattr(result, "success", True):
            error_msg = getattr(result, "error_message", "unknown")
            log.warning("scrape_failed", url=url, error=error_msg)
            return jobs
        # Prefer splitting by job cards (one entry per card) when HTML has job-detail links
        html = getattr(result, "html", None) or getattr(result, "cleaned_html", None)
        if isinstance(html, str) and html.strip():
            cards = _split_html_into_job_cards(html, url)
            if cards:
                source = "crawl4ai"
                jobs = [
                    {
                        "index": i + 1,
                        "source": source,
                        "url": c["url"],
                        "raw_text": c["raw_text"],
                        "title": c.get("title", ""),
                    }
                    for i, c in enumerate(cards)
                ]
        if not jobs:
            raw = getattr(result, "markdown", None)
            if hasattr(raw, "raw_markdown"):
                markdown = raw.raw_markdown or ""
            elif hasattr(raw, "fit_markdown") and raw.fit_markdown:
                markdown = raw.fit_markdown
            elif isinstance(raw, str):
                markdown = raw
            else:
                markdown = ""
            chunks = _chunk_markdown_into_jobs(markdown)
            chunks = [c for c in chunks if _looks_like_job_posting(c)][:MAX_JOBS]
            source = "crawl4ai"
            jobs = [
                {
                    "index": i + 1,
                    "source": source,
                    "url": url,
                    "raw_text": c,
                    "title": _title_from_markdown(c) or "",
                }
                for i, c in enumerate(chunks)
            ]
    return jobs


def _is_weworkremotely(url: str) -> bool:
    """True if URL is We Work Remotely (category or job page)."""
    return "weworkremotely.com" in url.lower()


def _is_remoteco(url: str) -> bool:
    """True if URL is Remote.co (category or job page)."""
    return "remote.co" in url.lower()


async def scrape_weworkremotely(entry_url: str) -> list[dict]:
    """
    Two-phase We Work Remotely: (1) Scrape category/list page for job links;
    (2) Scrape each job detail URL; one record per page.
    """
    jobs: list[dict] = []
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=entry_url)
        if not getattr(result, "success", True):
            log.warning("weworkremotely_discovery_failed", discovery_url=entry_url)
            return jobs
        job_urls = _extract_job_urls_weworkremotely(result)
        log.info("weworkremotely_discovery", discovery_url=entry_url, job_links_found=len(job_urls))
        for job_url in job_urls:
            markdown = await _scrape_one_job_page(crawler, job_url)
            if markdown:
                title = _title_from_markdown(markdown) or ""
                jobs.append({
                    "index": len(jobs) + 1,
                    "source": "crawl4ai",
                    "url": job_url,
                    "raw_text": markdown,
                    "title": title,
                })
            else:
                log.warning("weworkremotely_job_scrape_failed", job_url=job_url)
    return jobs


async def scrape_remoteco(entry_url: str) -> list[dict]:
    """
    Two-phase Remote.co: (1) Scrape category/list page for job links;
    (2) Scrape each job detail URL; one record per page.
    """
    jobs: list[dict] = []
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=entry_url)
        if not getattr(result, "success", True):
            log.warning("remoteco_discovery_failed", discovery_url=entry_url)
            return jobs
        job_urls = _extract_job_urls_remoteco(result)
        log.info("remoteco_discovery", discovery_url=entry_url, job_links_found=len(job_urls))
        for job_url in job_urls:
            markdown = await _scrape_one_job_page(crawler, job_url)
            if markdown:
                title = _title_from_markdown(markdown) or ""
                jobs.append({
                    "index": len(jobs) + 1,
                    "source": "crawl4ai",
                    "url": job_url,
                    "raw_text": markdown,
                    "title": title,
                })
            else:
                log.warning("remoteco_job_scrape_failed", job_url=job_url)
    return jobs


def run_scrape(url: str | None = None) -> int:
    """
    Run the scraper for one target URL and save raw output to staging.
    URL is the first entry in SCRAPING_TARGETS env (no default). Set SCRAPING_TARGETS in agents/.env.
    Failsafe: if the URL is unreachable, logs and returns 0 without scraping.
    Returns number of records written.
    """
    target = url or _get_target_url()
    if not target:
        log.warning("scrape_skipped", reason="no_target_url")
        return 0

    if not _check_url_reachable(target):
        log.warning(
            "scrape_aborted_url_unreachable",
            url=target,
            message="URL did not respond successfully; scrape not run.",
        )
        return 0

    fetch_started_at = datetime.now(timezone.utc)
    if _is_weworkremotely(target):
        jobs = asyncio.run(scrape_weworkremotely(target))
    elif _is_remoteco(target):
        jobs = asyncio.run(scrape_remoteco(target))
    else:
        jobs = asyncio.run(scrape_url(target))
    n = len(jobs)
    scraped_at = datetime.now(timezone.utc).isoformat()

    for j in jobs:
        j["scraped_at"] = scraped_at

    payload = {
        "source": "crawl4ai",
        "url": target,
        "fetch_started_at": fetch_started_at.isoformat(),
        "scraped_at": scraped_at,
        "record_count": n,
        "jobs": jobs,
    }

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_SCRAPE_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    log.info("raw_scrape_result", url=target, record_count=n)
    return n


if __name__ == "__main__":
    run_scrape()
