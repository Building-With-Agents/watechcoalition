"""
Scraper adapter: visits job search URLs, extracts job links, scrapes only valid job detail pages.
Output: 5–10 total postings across all targets; source from domain; raw_text = main content only.
"""
import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import structlog
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

# Load .env from repo root when run from agents/ or repo root
load_dotenv()
if not os.getenv("SCRAPING_TARGETS"):
    load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")

log = structlog.get_logger()
STAGING_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "staging"
OUTPUT_FILE = STAGING_DIR / "raw_scrape_sample.json"
MIN_JOBS = 5
MAX_JOBS = 10

# Path segments that indicate a job detail page (single job)
JOB_PATH_HINTS = ("job", "jobs", "careers", "position", "listing", "opening", "vacancy", "role", "remote-jobs")

# Path substrings that indicate non-job pages (marketing, company, nav)
NON_JOB_PATH_PARTS = (
    "about", "about-us", "contact", "privacy", "terms", "login", "signup", "register",
    "pricing", "for-employers", "employers", "post-a-job", "blog", "news", "press",
    "company", "companies", "our-story", "overview", "team", "careers-at",
    "faq", "help", "support", "resources", "learn-more", "how-it-works",
)


def _source_from_url(url: str) -> str:
    """Derive source identifier from domain (e.g. simplyhired.com -> simplyhired)."""
    parsed = urlparse(url)
    netloc = (parsed.netloc or "").lower().split(":")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    # take first part of host (e.g. subdomain.example.com -> subdomain; example.com -> example)
    parts = netloc.split(".")
    return parts[0] if parts else "unknown"


def _normalize_url(base_url: str, href: str) -> str | None:
    """Resolve href against base_url; return None if invalid."""
    if not href or href.strip() in ("", "#"):
        return None
    full = urljoin(base_url, href.strip())
    parsed = urlparse(full)
    if not parsed.scheme or not parsed.netloc:
        return None
    return parsed._replace(fragment="").geturl()


def _path_excluded(path: str) -> bool:
    """True if path suggests marketing, company overview, or navigation page."""
    path_lower = path.lower()
    return any(part in path_lower for part in NON_JOB_PATH_PARTS)


def _is_job_detail_url(url: str, search_netloc: str) -> bool:
    """
    True only if URL looks like an individual job posting page on the same domain.
    Excludes listing index pages, marketing, company, and nav.
    """
    parsed = urlparse(url)
    if (parsed.netloc or "").lower() != search_netloc:
        return False
    path = (parsed.path or "").strip("/")
    if not path:
        return False
    path_lower = path.lower()
    if _path_excluded(path_lower):
        return False
    # Must have a job-like segment
    if not any(hint in path_lower for hint in JOB_PATH_HINTS):
        return False
    # Reject bare listing index (e.g. /jobs, /careers) — need at least one more segment
    segments = [s for s in path.split("/") if s]
    if len(segments) < 2:
        return False
    # Reject assets
    if any(path_lower.endswith(ext) for ext in (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".css", ".js", ".xml")):
        return False
    return True


def _select_job_candidate_urls(links: list[dict], search_url: str, max_candidates: int = 30) -> list[str]:
    """From internal links, return URLs that pass job-detail filter (same domain, no marketing/company/nav)."""
    search_parsed = urlparse(search_url)
    search_netloc = (search_parsed.netloc or "").lower()
    seen: set[str] = set()
    out: list[str] = []
    for item in links:
        href = (item.get("href") or "").strip()
        url = _normalize_url(search_url, href)
        if not url or url in seen:
            continue
        if not _is_job_detail_url(url, search_netloc):
            continue
        seen.add(url)
        out.append(url)
        if len(out) >= max_candidates:
            break
    return out


# Markers that indicate start of core job content (main title / job description)
_JOB_CONTENT_START = re.compile(
    r"^(#+\s*)?(Job\s+Description|About\s+the\s+(role|job|position)|Description|"
    r"Full\s+job\s+description|Role\s+summary|Position\s+summary|Job\s+details|"
    r"Job\s+summary|Overview|The\s+role|The\s+position)\s*$",
    re.IGNORECASE,
)
# Nav/header phrases to skip at start (exact or near-exact line match)
_NAV_HEADER_PHRASES = (
    "home", "jobs", "companies", "sign in", "log in", "login", "sign up", "register",
    "post a job", "for employers", "employers", "browse jobs", "search jobs",
    "careers", "about", "contact", "blog", "resources", "help", "faq",
)
# Section headers that start boilerplate — content after these is dropped
_END_SECTION_PATTERN = re.compile(
    r"^\s*(#+\s*)?(Similar\s+Jobs?|Related\s+Jobs?|Recommended\s+Jobs?|Other\s+Jobs?|"
    r"More\s+Jobs?|Apply\s+for\s+this\s+Job|Share\s+this\s+Job|Footer|Navigation|"
    r"Cookie\s+(Policy|Notice)|Privacy\s+(Policy|Notice)|Terms\s+(of\s+Use)?|"
    r"All\s+Rights\s+Reserved|Subscribe|Follow\s+Us|©\s*|Sites?\s*we\s+follow)\s*$",
    re.IGNORECASE,
)
# Lines that are clearly footer/nav (drop)
_FOOTER_NAV_PATTERN = re.compile(
    r"^(\s*©\s*|\s*[\|\•]\s*|Privacy\s*\|\s*Terms|Cookie\s+Policy|All\s+rights\s+reserved)",
    re.IGNORECASE,
)
# Country/region list heuristic: line has many commas and looks like a list of places
_COUNTRY_LIST_MIN_COMMAS = 4
_COUNTRY_LIST_MIN_LEN = 50


def _looks_like_country_list_line(line: str) -> bool:
    """True if line appears to be a country/region list (comma-separated, long)."""
    s = line.strip()
    if len(s) < _COUNTRY_LIST_MIN_LEN:
        return False
    if s.count(",") < _COUNTRY_LIST_MIN_COMMAS:
        return False
    # Avoid cutting real job content (e.g. "requirements: a, b, c, d, e")
    if ":" in s or "•" in s or "- " in s:
        return False
    return True


def _is_nav_header_line(line: str) -> bool:
    """True if line looks like navigation or header (short, or matches nav phrases)."""
    s = line.strip()
    if len(s) > 60:
        return False
    lower = s.lower()
    return lower in _NAV_HEADER_PHRASES or any(
        lower == p or lower.startswith(p + " ") or lower.endswith(" " + p)
        for p in _NAV_HEADER_PHRASES
    )


def _extract_core_job_content(text: str) -> str:
    """
    Extract only core job posting content: start at job title/description, end before
    Similar Jobs/footer, remove nav/header, footer, country lists, and site-wide content.
    """
    if not text or not text.strip():
        return ""
    lines = [ln.rstrip() for ln in text.strip().split("\n")]

    # 1) Find start: job content marker, or first heading that looks like job title, or first substantial non-nav line
    start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if _JOB_CONTENT_START.match(s):
            start = i
            break
        if _is_nav_header_line(s):
            continue
        # Markdown heading that could be job title (# Title or ## Title)
        if re.match(r"^#+\s+.+", s) and 15 <= len(s) <= 200 and not _FOOTER_NAV_PATTERN.match(s):
            start = i
            break
        if len(s) >= 30 and not _FOOTER_NAV_PATTERN.match(s):
            start = i
            break

    # 2) Find end: first line that starts a boilerplate section (Similar Jobs, footer, etc.)
    end = len(lines)
    for i in range(start, len(lines)):
        if _END_SECTION_PATTERN.match(lines[i].strip()):
            end = i
            break
        if _FOOTER_NAV_PATTERN.match(lines[i].strip()) and len(lines[i].strip()) < 50:
            end = i
            break

    selected = lines[start:end]

    # 3) Drop country-list lines and trailing footer-like lines
    filtered = []
    for line in selected:
        s = line.strip()
        if not s:
            filtered.append(line)
            continue
        if _looks_like_country_list_line(s):
            continue
        if _FOOTER_NAV_PATTERN.match(s):
            continue
        filtered.append(line)

    # 4) Trim trailing short/footer lines
    while filtered:
        tail = filtered[-1].strip()
        if not tail:
            filtered.pop()
            continue
        if len(tail) < 25 or tail.startswith("©") or "|" in tail and len(tail) < 60:
            filtered.pop()
            continue
        break

    # 5) Collapse excessive blank lines, return single string
    result = "\n".join(filtered).strip()
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _is_likely_job_content(raw_text: str) -> bool:
    """Heuristic: content looks like a job description, not marketing/company page."""
    if not raw_text or len(raw_text.strip()) < 200:
        return False
    t = raw_text.lower()
    # Job pages often have these
    job_indicators = ("description", "requirements", "responsibilities", "qualifications", "apply", "experience", "salary", "remote", "location")
    # Marketing/company pages often have these
    non_job_indicators = ("contact us", "learn more", "get started", "sign up", "request a demo", "our mission", "our team", "about our company")
    score = sum(1 for w in job_indicators if w in t) - sum(1 for w in non_job_indicators if w in t)
    return score >= 1


async def get_job_candidate_urls(crawler: AsyncWebCrawler, search_url: str) -> list[str]:
    """Crawl search page and return candidate job detail URLs (same domain, filtered)."""
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    result = await crawler.arun(url=search_url, config=run_config)
    if not result or not getattr(result, "success", True):
        log.warning("search_page_failed", url=search_url, error=getattr(result, "error_message", "unknown"))
        return []
    links_data = getattr(result, "links", None) or {}
    internal = links_data.get("internal", []) if isinstance(links_data, dict) else []
    if not internal:
        log.warning("no_internal_links", url=search_url)
        return []
    urls = _select_job_candidate_urls(internal, search_url)
    log.info("job_candidates_extracted", search_url=search_url, count=len(urls))
    return urls


def _round_robin_urls(
    per_source: list[tuple[str, list[str]]], max_urls: int
) -> list[tuple[str, str]]:
    """
    Interleave URLs across sources: one from source 0, one from source 1, etc.
    Returns list of (job_url, source), no duplicate URLs, at most max_urls.
    """
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    indices = [0] * len(per_source)
    while len(result) < max_urls:
        added = False
        for i, (source, urls) in enumerate(per_source):
            if len(result) >= max_urls:
                break
            while indices[i] < len(urls):
                url = urls[indices[i]]
                indices[i] += 1
                if url not in seen:
                    seen.add(url)
                    result.append((url, source))
                    added = True
                    break
        if not added:
            break
    return result


async def scrape_and_validate_job_page(
    crawler: AsyncWebCrawler, job_url: str, source: str
) -> dict | None:
    """
    Scrape one URL. If it looks like a job detail page, return {source, scraped_url, timestamp, raw_text}.
    raw_text is main content only (boilerplate stripped). Otherwise return None.
    """
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    result = await crawler.arun(url=job_url, config=run_config)
    if not result or not getattr(result, "success", True):
        log.warning("job_page_failed", url=job_url, error=getattr(result, "error_message", "unknown"))
        return None

    raw_md = getattr(result.markdown, "raw_markdown", None) or getattr(result.markdown, "fit_markdown", None)
    text = raw_md if isinstance(raw_md, str) else (getattr(result, "markdown", None) or "")
    if not text:
        text = getattr(result, "cleaned_html", "") or ""
    text = (text or "").strip()

    if not _is_likely_job_content(text):
        log.info("page_rejected_not_job", url=job_url, reason="content_heuristic")
        return None

    raw_text = _extract_core_job_content(text)
    if len(raw_text.strip()) < 150:
        log.info("page_rejected_too_short", url=job_url)
        return None

    return {
        "source": source,
        "scraped_url": job_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_text": raw_text.strip(),
    }


async def scrape_all(search_urls: list[str]) -> list[dict]:
    """
    Collect job links per source, then process in round-robin order across sources.
    Stop when global limit (MAX_JOBS) is reached or all sources exhausted.
    Ensures fair representation across sources (no per-source limits, no favoring first).
    """
    async with AsyncWebCrawler() as crawler:
        # Phase 1: collect job candidate URLs for each source
        per_source: list[tuple[str, list[str]]] = []
        for search_url in search_urls:
            log.info("scrape_start", url=search_url)
            candidate_urls = await get_job_candidate_urls(crawler, search_url)
            source = _source_from_url(search_url)
            per_source.append((source, candidate_urls))
            log.info("job_candidates_collected", search_url=search_url, source=source, count=len(candidate_urls))

        if not per_source:
            return []

        # Phase 2: build round-robin sequence (one from A, one from B, ...) — cap candidates to try
        max_candidates = max(MAX_JOBS * 3, 30)
        round_robin = _round_robin_urls(per_source, max_candidates)
        log.info("round_robin_built", total_candidates=len(round_robin), source_count=len(per_source))

        # Phase 3: scrape in round-robin order until limit or exhausted
        all_postings: list[dict] = []
        for job_url, source in round_robin:
            if len(all_postings) >= MAX_JOBS:
                break
            record = await scrape_and_validate_job_page(crawler, job_url, source)
            if record:
                all_postings.append(record)
                log.info("raw_scrape_result", url=job_url, source=source, record_count=len(all_postings))
        return all_postings[:MAX_JOBS]


def main() -> None:
    targets = os.getenv("SCRAPING_TARGETS", "").strip()
    if not targets:
        log.error("scrape_config_missing", message="SCRAPING_TARGETS is not set")
        raise SystemExit("ERROR: SCRAPING_TARGETS is not set. Set it in .env at the repo root.")
    search_urls = [u.strip() for u in targets.split(",") if u.strip()]
    if not search_urls:
        log.error("scrape_config_missing", message="No valid URLs in SCRAPING_TARGETS")
        raise SystemExit("ERROR: No valid URLs in SCRAPING_TARGETS.")

    postings = asyncio.run(scrape_all(search_urls))

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(postings, f, ensure_ascii=False, indent=2)

    log.info("scrape_complete", url_count=len(search_urls), total_record_count=len(postings))


if __name__ == "__main__":
    main()
